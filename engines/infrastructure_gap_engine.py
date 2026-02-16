"""
infrastructure_gap_engine.py

Phase 2 — Samagra Shiksha Norm-Based Classroom Gap Engine (Bulk SQL)

Computes required_class_rooms and classroom_gap for every school-year
record in infrastructure_details using a single bulk SQL UPDATE with
CASE-based Andhra Pradesh Samagra Shiksha classroom norms.

No row fetching or Python loops — all computation runs server-side.

Norms (students per classroom):
  Category 1  (Primary, 1–5)                          → 30
  Category 2  (Primary + Upper Primary, 1–8)           → 30  (blended)
  Category 3  (Primary to Higher Secondary, 1–12)      → 30  (blended)
  Category 4  (Upper Primary only, 5–8)                → 35
  Category 5  (Upper Primary to Higher Secondary, 6–12)→ 35
  Category 6  (Primary to Secondary, 1–10)             → 30  (blended)
  Category 7  (Upper Primary to Secondary, 6–10)       → 35
  Category 8  (Secondary only, 9–10)                   → 40
  Category 10 (Secondary to Higher Secondary, 9–12)    → 40
  Category 11 (Higher Secondary only, 11–12)           → 40

Idempotent — safe to re-run; always overwrites computed columns.
"""

import os
import sys
import time

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ── Bulk UPDATE statement ────────────────────────────────────────────────────

NORM_CASE = """
    CASE
        WHEN s.school_category = '1'  THEN 30
        WHEN s.school_category = '2'  THEN 30
        WHEN s.school_category = '3'  THEN 30
        WHEN s.school_category = '4'  THEN 35
        WHEN s.school_category = '5'  THEN 35
        WHEN s.school_category = '6'  THEN 30
        WHEN s.school_category = '7'  THEN 35
        WHEN s.school_category = '8'  THEN 40
        WHEN s.school_category = '10' THEN 40
        WHEN s.school_category = '11' THEN 40
        ELSE 30
    END
"""

BULK_UPDATE_SQL = text(f"""
    UPDATE infrastructure_details i
    JOIN yearly_metrics y
        ON  i.school_id    = y.school_id
        AND i.academic_year = y.academic_year
    JOIN schools s
        ON  s.school_id    = i.school_id
    SET
        i.required_class_rooms = CEIL(y.total_enrolment / {NORM_CASE}),
        i.classroom_gap = GREATEST(
            CEIL(y.total_enrolment / {NORM_CASE})
            - IFNULL(i.usable_class_rooms, 0),
            0
        )
    WHERE i.academic_year = :year
""")

# ── Summary queries ──────────────────────────────────────────────────────────

STATS_SQL = text("""
    SELECT
        COUNT(*)                                   AS total_records,
        SUM(CASE WHEN classroom_gap > 0 THEN 1 ELSE 0 END) AS deficit_count,
        ROUND(AVG(CASE WHEN classroom_gap > 0 THEN classroom_gap END), 2) AS avg_gap
    FROM infrastructure_details
""")

TOP_DISTRICTS_SQL = text("""
    SELECT
        s.district,
        SUM(i.classroom_gap)  AS cumulative_gap,
        COUNT(*)              AS school_years
    FROM infrastructure_details i
    JOIN schools s ON i.school_id = s.school_id
    WHERE i.classroom_gap > 0
    GROUP BY s.district
    ORDER BY cumulative_gap DESC
    LIMIT 10
""")

YEARS_SQL = text("""
    SELECT DISTINCT academic_year FROM infrastructure_details ORDER BY academic_year
""")


# ── Performance indexes ──────────────────────────────────────────────────────

INDEX_STATEMENTS = [
    (
        "idx_infra_school_year",
        "CREATE INDEX idx_infra_school_year "
        "ON infrastructure_details (school_id, academic_year)"
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
    print("Step 1/4 — Ensuring performance indexes...")
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

    # ── Step 1: Ensure performance indexes ───────────────────────────────
    _ensure_indexes(engine)

    # ── Step 2: Ensure classroom_gap column exists ───────────────────────
    print("Step 2/4 — Ensuring classroom_gap column exists...")
    with engine.begin() as conn:
        try:
            conn.execute(text(
                "ALTER TABLE infrastructure_details "
                "ADD COLUMN classroom_gap INT NULL"
            ))
            print("  [OK] Column 'classroom_gap' added.\n")
        except Exception:
            print("  [OK] Column 'classroom_gap' already present.\n")

    # ── Step 3: Bulk UPDATE (batched per academic year) ────────────────
    print("Step 3/4 — Running bulk SQL UPDATEs (batched per year)...")
    t0 = time.time()

    # Fetch distinct years
    with engine.connect() as conn:
        years = [r["academic_year"] for r in conn.execute(YEARS_SQL).mappings().all()]

    total_affected = 0
    for yr in years:
        t_yr = time.time()
        with engine.begin() as conn:
            result = conn.execute(BULK_UPDATE_SQL, {"year": yr})
            affected = result.rowcount
            total_affected += affected
        print(f"  [OK] {yr}: {affected:,} rows  ({time.time() - t_yr:.1f}s)")

    elapsed = time.time() - t0
    print(f"\n  Total: {total_affected:,} rows updated in {elapsed:.1f}s.\n")

    # ── Step 4: Summary (printed exactly once) ─────────────────────────
    print("Step 4/4 — Generating summary...")

    with engine.connect() as conn:
        stats = conn.execute(STATS_SQL).mappings().first()
        top_districts = conn.execute(TOP_DISTRICTS_SQL).mappings().all()

    sep = "=" * 56
    dash = "-" * 48
    lines = [
        "",
        sep,
        "Infrastructure Gap Engine — Summary",
        sep,
        f"Total school-year records  : {int(stats['total_records']):,}",
        f"Records with deficit       : {int(stats['deficit_count']):,}",
        f"Average classroom gap      : {stats['avg_gap']}",
        "",
        "Top 10 Districts by Cumulative Classroom Gap:",
        dash,
    ]
    seen = set()
    for d in top_districts:
        district = str(d["district"] or "").strip()
        if not district or district in seen:
            continue
        seen.add(district)
        lines.append(f"{district:25s} gap: {int(d['cumulative_gap']):>7,}")
    lines.append(dash)

    print("\n".join(lines))


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 56)
    print("  School AI BAV — Infrastructure Gap Engine (v2.1)")
    print("=" * 56 + "\n")
    run()
