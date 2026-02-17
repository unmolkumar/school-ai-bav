"""
district_compliance_engine.py

Phase 8 — District Compliance Index (Bulk SQL)

Aggregates school-level risk and infrastructure data up to the district
level, producing a single compliance scorecard per district per year.

Creates and populates the district_compliance_index table:
  - total_schools           : COUNT of schools in the district-year
  - avg_risk_score          : mean risk_score across district schools
  - pct_high_critical       : % of schools rated HIGH or CRITICAL
  - total_classroom_deficit : SUM of classroom_gap across district
  - total_teacher_deficit   : SUM of teacher_gap across district
  - total_enrolment         : SUM of enrolment across district
  - avg_classroom_condition : mean classroom_condition_score
  - yoy_risk_improvement    : change in avg_risk_score vs prior year
  - district_rank           : RANK() by avg_risk_score DESC per year
  - compliance_grade        : A / B / C / D / F based on avg_risk

All computation runs server-side via aggregate + window functions.
No Python row loops. Idempotent — safe to re-run.
"""

import os
import sys
import time

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ── Table DDL ────────────────────────────────────────────────────────────────

CREATE_TABLE_SQL = text("""
    CREATE TABLE IF NOT EXISTS district_compliance_index (
        id                      INT AUTO_INCREMENT PRIMARY KEY,
        district                VARCHAR(100) NOT NULL,
        academic_year           VARCHAR(20)  NOT NULL,
        total_schools           INT,
        avg_risk_score          FLOAT,
        pct_high_critical       FLOAT,
        total_classroom_deficit INT,
        total_teacher_deficit   INT,
        total_enrolment         BIGINT,
        avg_classroom_condition FLOAT,
        yoy_risk_improvement    FLOAT,
        district_rank           INT,
        compliance_grade        VARCHAR(5)
    )
""")

# ── Indexes ──────────────────────────────────────────────────────────────────

INDEX_STATEMENTS = [
    (
        "idx_dci_district_year",
        "CREATE INDEX idx_dci_district_year "
        "ON district_compliance_index (district, academic_year)"
    ),
    (
        "idx_dci_rank",
        "CREATE INDEX idx_dci_rank "
        "ON district_compliance_index (academic_year, district_rank)"
    ),
]

# ── Core INSERT: aggregate school data per district-year ─────────────────────

POPULATE_SQL = text("""
    INSERT INTO district_compliance_index
        (district, academic_year, total_schools, avg_risk_score,
         pct_high_critical, total_classroom_deficit, total_teacher_deficit,
         total_enrolment, avg_classroom_condition, compliance_grade)
    SELECT
        s.district,
        i.academic_year,
        COUNT(DISTINCT i.school_id)                                     AS total_schools,
        ROUND(AVG(i.risk_score), 4)                                     AS avg_risk_score,
        ROUND(
            SUM(CASE WHEN i.risk_level IN ('HIGH','CRITICAL') THEN 1 ELSE 0 END)
            * 100.0 / NULLIF(COUNT(*), 0),
            2
        )                                                               AS pct_high_critical,
        SUM(CASE WHEN i.classroom_gap > 0 THEN i.classroom_gap ELSE 0 END)
                                                                        AS total_classroom_deficit,
        SUM(CASE WHEN t.teacher_gap > 0 THEN t.teacher_gap ELSE 0 END)
                                                                        AS total_teacher_deficit,
        SUM(y.total_enrolment)                                          AS total_enrolment,
        ROUND(AVG(i.classroom_condition_score), 4)                      AS avg_classroom_condition,
        CASE
            WHEN AVG(i.risk_score) <= 0.15 THEN 'A'
            WHEN AVG(i.risk_score) <= 0.30 THEN 'B'
            WHEN AVG(i.risk_score) <= 0.50 THEN 'C'
            WHEN AVG(i.risk_score) <= 0.75 THEN 'D'
            ELSE 'F'
        END                                                             AS compliance_grade
    FROM infrastructure_details i
    JOIN schools s          ON i.school_id = s.school_id
    LEFT JOIN teacher_metrics t ON i.school_id = t.school_id
                                AND i.academic_year = t.academic_year
    LEFT JOIN yearly_metrics y  ON i.school_id = y.school_id
                                AND i.academic_year = y.academic_year
    WHERE i.risk_score IS NOT NULL
      AND i.academic_year = :year
    GROUP BY s.district, i.academic_year
""")

# ── YoY improvement via LAG on own table (requires all years populated) ──────

YOY_SQL = text("""
    UPDATE district_compliance_index dci
    JOIN (
        SELECT
            district,
            academic_year,
            avg_risk_score - LAG(avg_risk_score, 1) OVER (
                PARTITION BY district ORDER BY academic_year
            ) AS delta
        FROM district_compliance_index
    ) derived
        ON  dci.district      = derived.district
        AND dci.academic_year  = derived.academic_year
    SET dci.yoy_risk_improvement = derived.delta
""")

# ── District rank via RANK() per year ────────────────────────────────────────

RANK_SQL = text("""
    UPDATE district_compliance_index dci
    JOIN (
        SELECT
            district,
            academic_year,
            RANK() OVER (
                PARTITION BY academic_year
                ORDER BY avg_risk_score DESC
            ) AS rnk
        FROM district_compliance_index
    ) derived
        ON  dci.district      = derived.district
        AND dci.academic_year  = derived.academic_year
    SET dci.district_rank = derived.rnk
""")

# ── Distinct years ───────────────────────────────────────────────────────────

YEARS_SQL = text("""
    SELECT DISTINCT academic_year
    FROM infrastructure_details
    WHERE risk_score IS NOT NULL
    ORDER BY academic_year
""")

# ── Summary ──────────────────────────────────────────────────────────────────

STATS_SQL = text("""
    SELECT
        COUNT(*)                                              AS total_records,
        COUNT(DISTINCT district)                              AS total_districts,
        ROUND(AVG(avg_risk_score), 4)                         AS overall_avg_risk,
        ROUND(AVG(pct_high_critical), 2)                      AS avg_pct_high_critical,
        SUM(total_classroom_deficit)                           AS grand_classroom_deficit,
        SUM(total_teacher_deficit)                             AS grand_teacher_deficit,
        SUM(CASE WHEN compliance_grade = 'A' THEN 1 ELSE 0 END) AS grade_a,
        SUM(CASE WHEN compliance_grade = 'B' THEN 1 ELSE 0 END) AS grade_b,
        SUM(CASE WHEN compliance_grade = 'C' THEN 1 ELSE 0 END) AS grade_c,
        SUM(CASE WHEN compliance_grade = 'D' THEN 1 ELSE 0 END) AS grade_d,
        SUM(CASE WHEN compliance_grade = 'F' THEN 1 ELSE 0 END) AS grade_f
    FROM district_compliance_index
""")

TOP_RISK_DISTRICTS_SQL = text("""
    SELECT
        district,
        academic_year,
        avg_risk_score,
        pct_high_critical,
        total_classroom_deficit,
        total_teacher_deficit,
        district_rank,
        compliance_grade
    FROM district_compliance_index
    WHERE academic_year = (
        SELECT MAX(academic_year) FROM district_compliance_index
    )
    ORDER BY avg_risk_score DESC
    LIMIT 10
""")


# ── Main engine ──────────────────────────────────────────────────────────────

def run():
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not found in .env")
        sys.exit(1)

    engine = create_engine(
        DATABASE_URL, echo=False,
        pool_recycle=280, pool_pre_ping=True,
        connect_args={"connect_timeout": 30},
    )

    # ── Step 1: Create table ─────────────────────────────────────────────
    print("Step 1/6 — Ensuring district_compliance_index table exists...")
    with engine.begin() as conn:
        conn.execute(CREATE_TABLE_SQL)
    print("  [OK] Table ready.\n")

    # ── Step 2: Indexes ──────────────────────────────────────────────────
    print("Step 2/6 — Ensuring indexes...")
    with engine.begin() as conn:
        for name, ddl in INDEX_STATEMENTS:
            try:
                conn.execute(text(ddl))
                print(f"  [OK] Index '{name}' created.")
            except Exception:
                print(f"  [OK] Index '{name}' already exists.")
    print()

    # ── Step 3: Clear ────────────────────────────────────────────────────
    print("Step 3/6 — Clearing existing data (idempotent reset)...")
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM district_compliance_index"))
    print("  [OK] Cleared.\n")

    # ── Step 4: Populate per year ────────────────────────────────────────
    with engine.connect() as conn:
        years = [r["academic_year"] for r in conn.execute(YEARS_SQL).mappings().all()]

    print("Step 4/6 — Aggregating district compliance (batched per year)...")
    t0 = time.time()
    total = 0
    for yr in years:
        t_yr = time.time()
        with engine.begin() as conn:
            result = conn.execute(POPULATE_SQL, {"year": yr})
            affected = result.rowcount
            total += affected
        print(f"  [OK] {yr}: {affected} districts  ({time.time() - t_yr:.1f}s)")
    print(f"\n  Aggregated: {total} district-year records in {time.time() - t0:.1f}s.\n")

    # ── Step 5: YoY improvement ──────────────────────────────────────────
    print("Step 5/6 — Computing YoY risk improvement...")
    t0 = time.time()
    with engine.begin() as conn:
        conn.execute(YOY_SQL)
    print(f"  [OK] YoY deltas computed  ({time.time() - t0:.1f}s)\n")

    # ── Step 6: District ranks ───────────────────────────────────────────
    print("Step 6/6 — Computing district ranks...")
    t0 = time.time()
    with engine.begin() as conn:
        conn.execute(RANK_SQL)
    print(f"  [OK] Ranks computed  ({time.time() - t0:.1f}s)\n")

    # ── Summary ──────────────────────────────────────────────────────────
    print("Generating summary...")
    with engine.connect() as conn:
        stats = conn.execute(STATS_SQL).mappings().first()
        top_risk = conn.execute(TOP_RISK_DISTRICTS_SQL).mappings().all()

    sep = "=" * 62
    dash = "-" * 58
    lines = [
        "", sep,
        "District Compliance Index — Summary",
        sep,
        f"Total district-year records : {int(stats['total_records'])}",
        f"Unique districts            : {int(stats['total_districts'])}",
        f"Overall avg risk score      : {stats['overall_avg_risk']}",
        f"Avg pct HIGH+CRITICAL       : {stats['avg_pct_high_critical']}%",
        f"Grand classroom deficit     : {int(stats['grand_classroom_deficit']):,}",
        f"Grand teacher deficit       : {int(stats['grand_teacher_deficit']):,}",
        "",
        "Compliance Grades (all years):",
        f"  A (<=0.15) : {int(stats['grade_a'])}",
        f"  B (<=0.30) : {int(stats['grade_b'])}",
        f"  C (<=0.50) : {int(stats['grade_c'])}",
        f"  D (<=0.75) : {int(stats['grade_d'])}",
        f"  F (>0.75)  : {int(stats['grade_f'])}",
        "",
        "Top 10 Highest-Risk Districts (latest year):",
        dash,
    ]
    for d in top_risk:
        district = str(d["district"] or "").strip()
        lines.append(
            f"  #{int(d['district_rank']):>2}  {district:22s}"
            f"  risk: {d['avg_risk_score']:.4f}"
            f"  H+C: {d['pct_high_critical']:>5.1f}%"
            f"  cr_def: {int(d['total_classroom_deficit']):>6,}"
            f"  grade: {d['compliance_grade']}"
        )
    lines.append(dash)
    print("\n".join(lines))


if __name__ == "__main__":
    print("=" * 62)
    print("  School AI BAV — District Compliance Engine (v1.0)")
    print("=" * 62 + "\n")
    run()
