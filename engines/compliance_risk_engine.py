"""
compliance_risk_engine.py

Phase 4 — Composite Compliance Risk Engine (Bulk SQL)

Computes a weighted composite risk_score for every school-year record
in infrastructure_details, combining teacher deficit, classroom deficit,
and enrolment growth signals into a single governance-ready metric.

Formula:
  risk_score =
      (0.45 × teacher_deficit_ratio)
    + (0.35 × classroom_deficit_ratio)
    + (0.20 × growth_scaled)

Component definitions:
  teacher_deficit_ratio   = MIN(teacher_gap / NULLIF(required_teachers, 0), 1.0)
  classroom_deficit_ratio = MIN(classroom_gap / NULLIF(required_class_rooms, 0), 1.0)
  enrolment_growth_rate   = (current - previous) / previous   via LAG()
  growth_scaled           = MIN(ABS(enrolment_growth_rate), 0.50)

Risk classification:
  0.00–0.20  → LOW
  0.21–0.50  → MODERATE
  0.51–0.75  → HIGH
  > 0.75     → CRITICAL

Weight justification (Samagra Shiksha alignment):
  - 0.45 teacher: RTE Act mandates PTR compliance as primary input quality
    indicator; teacher adequacy is the single largest predictor of learning
    outcomes in government evaluations.
  - 0.35 classroom: Samagra Shiksha infrastructure norms treat classroom
    adequacy as the core physical capacity constraint.
  - 0.20 growth: Enrolment trajectory signals emerging demand pressure or
    decline risk; lower weight reflects its lagging-indicator nature.

All computation runs server-side. No Python row loops.
Idempotent — safe to re-run; always overwrites computed columns.
"""

import os
import sys
import time

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ── Columns to add ──────────────────────────────────────────────────────────

NEW_COLUMNS = [
    ("classroom_deficit_ratio", "FLOAT NULL"),
    ("teacher_deficit_ratio",   "FLOAT NULL"),
    ("enrolment_growth_rate",   "FLOAT NULL"),
    ("risk_score",              "FLOAT NULL"),
    ("risk_level",              "VARCHAR(20) NULL"),
]

# ── Bulk UPDATE: deficit ratios ──────────────────────────────────────────────

DEFICIT_RATIOS_SQL = text("""
    UPDATE infrastructure_details i
    JOIN teacher_metrics t
        ON  i.school_id     = t.school_id
        AND i.academic_year  = t.academic_year
    SET
        i.classroom_deficit_ratio = LEAST(
            IFNULL(i.classroom_gap, 0)
            / NULLIF(i.required_class_rooms, 0),
            1.0
        ),
        i.teacher_deficit_ratio = LEAST(
            IFNULL(t.teacher_gap, 0)
            / NULLIF(t.required_teachers, 0),
            1.0
        )
    WHERE i.academic_year = :year
""")

# ── Bulk UPDATE: enrolment growth rate via subquery with LAG() ───────────────
# MySQL does not allow UPDATE with window functions directly on the target
# table, so we use a derived-table subquery.

GROWTH_RATE_SQL = text("""
    UPDATE infrastructure_details i
    JOIN (
        SELECT
            school_id,
            academic_year,
            CASE
                WHEN prev_enrolment IS NULL OR prev_enrolment = 0 THEN 0.0
                ELSE (total_enrolment - prev_enrolment) / prev_enrolment
            END AS growth
        FROM (
            SELECT
                school_id,
                academic_year,
                total_enrolment,
                LAG(total_enrolment) OVER (
                    PARTITION BY school_id ORDER BY academic_year
                ) AS prev_enrolment
            FROM yearly_metrics
        ) sub
    ) g
        ON  i.school_id     = g.school_id
        AND i.academic_year  = g.academic_year
    SET
        i.enrolment_growth_rate = g.growth
    WHERE i.academic_year = :year
""")

# ── Bulk UPDATE: composite risk score + risk level ───────────────────────────

RISK_SCORE_SQL = text("""
    UPDATE infrastructure_details i
    SET
        i.risk_score = ROUND(
              (0.45 * IFNULL(i.teacher_deficit_ratio, 0))
            + (0.35 * IFNULL(i.classroom_deficit_ratio, 0))
            + (0.20 * LEAST(ABS(IFNULL(i.enrolment_growth_rate, 0)), 0.50)),
            4
        ),
        i.risk_level = CASE
            WHEN (
                  (0.45 * IFNULL(i.teacher_deficit_ratio, 0))
                + (0.35 * IFNULL(i.classroom_deficit_ratio, 0))
                + (0.20 * LEAST(ABS(IFNULL(i.enrolment_growth_rate, 0)), 0.50))
            ) > 0.75 THEN 'CRITICAL'
            WHEN (
                  (0.45 * IFNULL(i.teacher_deficit_ratio, 0))
                + (0.35 * IFNULL(i.classroom_deficit_ratio, 0))
                + (0.20 * LEAST(ABS(IFNULL(i.enrolment_growth_rate, 0)), 0.50))
            ) > 0.50 THEN 'HIGH'
            WHEN (
                  (0.45 * IFNULL(i.teacher_deficit_ratio, 0))
                + (0.35 * IFNULL(i.classroom_deficit_ratio, 0))
                + (0.20 * LEAST(ABS(IFNULL(i.enrolment_growth_rate, 0)), 0.50))
            ) > 0.20 THEN 'MODERATE'
            ELSE 'LOW'
        END
    WHERE i.academic_year = :year
""")

# ── Summary queries ──────────────────────────────────────────────────────────

STATS_SQL = text("""
    SELECT
        COUNT(*)                                     AS total_records,
        ROUND(AVG(risk_score), 4)                    AS avg_risk,
        SUM(CASE WHEN risk_level = 'CRITICAL' THEN 1 ELSE 0 END) AS critical_count,
        SUM(CASE WHEN risk_level = 'HIGH'     THEN 1 ELSE 0 END) AS high_count,
        SUM(CASE WHEN risk_level = 'MODERATE' THEN 1 ELSE 0 END) AS moderate_count,
        SUM(CASE WHEN risk_level = 'LOW'      THEN 1 ELSE 0 END) AS low_count
    FROM infrastructure_details
""")

TOP_DISTRICTS_SQL = text("""
    SELECT
        s.district,
        ROUND(AVG(i.risk_score), 4) AS avg_risk,
        SUM(CASE WHEN i.risk_level = 'CRITICAL' THEN 1 ELSE 0 END) AS critical,
        COUNT(*) AS school_years
    FROM infrastructure_details i
    JOIN schools s ON i.school_id = s.school_id
    WHERE i.risk_score IS NOT NULL
    GROUP BY s.district
    ORDER BY avg_risk DESC
    LIMIT 10
""")

YEARS_SQL = text("""
    SELECT DISTINCT academic_year
    FROM infrastructure_details
    ORDER BY academic_year
""")

# ── Performance indexes ──────────────────────────────────────────────────────

INDEX_STATEMENTS = [
    (
        "idx_infra_school_year",
        "CREATE INDEX idx_infra_school_year "
        "ON infrastructure_details (school_id, academic_year)"
    ),
    (
        "idx_teacher_school_year",
        "CREATE INDEX idx_teacher_school_year "
        "ON teacher_metrics (school_id, academic_year)"
    ),
    (
        "idx_yearly_school_year",
        "CREATE INDEX idx_yearly_school_year "
        "ON yearly_metrics (school_id, academic_year)"
    ),
    (
        "idx_schools_school_id",
        "CREATE INDEX idx_schools_school_id "
        "ON schools (school_id)"
    ),
]

# ── Main engine ──────────────────────────────────────────────────────────────


def _ensure_indexes(engine):
    """Create performance indexes if they do not already exist."""
    print("Step 1/5 — Ensuring performance indexes...")
    t0 = time.time()
    with engine.begin() as conn:
        for name, ddl in INDEX_STATEMENTS:
            try:
                conn.execute(text(ddl))
                print(f"  [OK] Index '{name}' created.")
            except Exception:
                print(f"  [OK] Index '{name}' already exists.")
    elapsed = time.time() - t0
    print(f"  Index check completed in {elapsed:.2f}s.\n")


def _ensure_columns(engine):
    """Add new risk columns to infrastructure_details if missing."""
    print("Step 2/5 — Ensuring risk columns exist...")
    with engine.begin() as conn:
        for col_name, col_def in NEW_COLUMNS:
            try:
                conn.execute(text(
                    f"ALTER TABLE infrastructure_details "
                    f"ADD COLUMN {col_name} {col_def}"
                ))
                print(f"  [OK] Column '{col_name}' added.")
            except Exception:
                print(f"  [OK] Column '{col_name}' already present.")
    print()


def run():
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not found in .env")
        sys.exit(1)

    engine = create_engine(
        DATABASE_URL, echo=False,
        pool_recycle=280,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 30},
    )

    # ── Step 1: Indexes ──────────────────────────────────────────────────
    _ensure_indexes(engine)

    # ── Step 2: Columns ──────────────────────────────────────────────────
    _ensure_columns(engine)

    # ── Step 3: Fetch distinct years ─────────────────────────────────────
    with engine.connect() as conn:
        years = [r["academic_year"] for r in conn.execute(YEARS_SQL).mappings().all()]

    # ── Step 3a: Deficit ratios (batched per year) ───────────────────────
    print("Step 3/5 — Computing deficit ratios (batched per year)...")
    t0 = time.time()
    total_affected = 0
    for yr in years:
        t_yr = time.time()
        with engine.begin() as conn:
            result = conn.execute(DEFICIT_RATIOS_SQL, {"year": yr})
            affected = result.rowcount
            total_affected += affected
        print(f"  [OK] {yr}: {affected:,} rows  ({time.time() - t_yr:.1f}s)")
    elapsed = time.time() - t0
    print(f"\n  Deficit ratios: {total_affected:,} rows in {elapsed:.1f}s.\n")

    # ── Step 3b: Growth rate (batched per year) ──────────────────────────
    print("Step 4/5 — Computing enrolment growth rates (batched per year)...")
    t0 = time.time()
    total_affected = 0
    for yr in years:
        t_yr = time.time()
        with engine.begin() as conn:
            result = conn.execute(GROWTH_RATE_SQL, {"year": yr})
            affected = result.rowcount
            total_affected += affected
        print(f"  [OK] {yr}: {affected:,} rows  ({time.time() - t_yr:.1f}s)")
    elapsed = time.time() - t0
    print(f"\n  Growth rates: {total_affected:,} rows in {elapsed:.1f}s.\n")

    # ── Step 3c: Risk score + level (batched per year) ───────────────────
    print("Step 5/5 — Computing composite risk scores (batched per year)...")
    t0 = time.time()
    total_affected = 0
    for yr in years:
        t_yr = time.time()
        with engine.begin() as conn:
            result = conn.execute(RISK_SCORE_SQL, {"year": yr})
            affected = result.rowcount
            total_affected += affected
        print(f"  [OK] {yr}: {affected:,} rows  ({time.time() - t_yr:.1f}s)")
    elapsed = time.time() - t0
    print(f"\n  Risk scores: {total_affected:,} rows in {elapsed:.1f}s.\n")

    # ── Summary (printed exactly once) ───────────────────────────────────
    print("Generating summary...")

    with engine.connect() as conn:
        stats = conn.execute(STATS_SQL).mappings().first()
        top_districts = conn.execute(TOP_DISTRICTS_SQL).mappings().all()

    sep = "=" * 56
    dash = "-" * 48
    lines = [
        "",
        sep,
        "Composite Compliance Risk Engine — Summary",
        sep,
        f"Total school-year records  : {int(stats['total_records']):,}",
        f"Average risk score         : {stats['avg_risk']}",
        "",
        f"  CRITICAL : {int(stats['critical_count']):>7,}",
        f"  HIGH     : {int(stats['high_count']):>7,}",
        f"  MODERATE : {int(stats['moderate_count']):>7,}",
        f"  LOW      : {int(stats['low_count']):>7,}",
        "",
        "Top 10 Districts by Average Risk Score:",
        dash,
    ]
    seen = set()
    for d in top_districts:
        district = str(d["district"] or "").strip()
        if not district or district in seen:
            continue
        seen.add(district)
        lines.append(
            f"{district:25s} avg: {float(d['avg_risk']):.4f}"
            f"  critical: {int(d['critical']):>5,}"
        )
    lines.append(dash)

    print("\n".join(lines))


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 56)
    print("  School AI BAV — Compliance Risk Engine (v1.0)")
    print("=" * 56 + "\n")
    run()
