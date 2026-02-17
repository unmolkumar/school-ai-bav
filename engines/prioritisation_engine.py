"""
prioritisation_engine.py

Phase 5 — School Prioritisation Engine (Bulk SQL)

Converts risk_score (Phase 4) into actionable state-wide and district-level
rankings with persistent high-risk detection and priority bucketing.

Creates and populates the school_priority_index table:
  - state_rank        : RANK() OVER (ORDER BY risk_score DESC) per year
  - district_rank     : RANK() OVER (PARTITION BY district ORDER BY ...) per year
  - priority_bucket   : Top 5% / Top 10% / Top 20% / Standard
  - persistent_high_risk_flag : 1 if school has 3+ consecutive HIGH/CRITICAL years

All computation runs server-side via window functions.
No Python row loops. Idempotent — safe to re-run.
"""

import os
import sys
import time

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ── Table DDL ────────────────────────────────────────────────────────────────

CREATE_TABLE_SQL = text("""
    CREATE TABLE IF NOT EXISTS school_priority_index (
        id                        INT AUTO_INCREMENT PRIMARY KEY,
        school_id                 VARCHAR(50)  NOT NULL,
        academic_year             VARCHAR(20)  NOT NULL,
        risk_score                FLOAT,
        state_rank                INT,
        district_rank             INT,
        persistent_high_risk_flag TINYINT DEFAULT 0,
        priority_bucket           VARCHAR(20)
    )
""")

# ── Index ────────────────────────────────────────────────────────────────────

INDEX_STATEMENTS = [
    (
        "idx_priority_school_year",
        "CREATE INDEX idx_priority_school_year "
        "ON school_priority_index (school_id, academic_year)"
    ),
]

# ── Populate: ranks + buckets via INSERT ... SELECT with window functions ────

POPULATE_SQL = text("""
    INSERT INTO school_priority_index
        (school_id, academic_year, risk_score,
         state_rank, district_rank, priority_bucket)
    SELECT
        i.school_id,
        i.academic_year,
        i.risk_score,
        RANK() OVER (
            ORDER BY i.risk_score DESC
        ) AS state_rank,
        RANK() OVER (
            PARTITION BY s.district
            ORDER BY i.risk_score DESC
        ) AS district_rank,
        CASE
            WHEN PERCENT_RANK() OVER (
                ORDER BY i.risk_score DESC
            ) <= 0.05 THEN 'TOP_5'
            WHEN PERCENT_RANK() OVER (
                ORDER BY i.risk_score DESC
            ) <= 0.10 THEN 'TOP_10'
            WHEN PERCENT_RANK() OVER (
                ORDER BY i.risk_score DESC
            ) <= 0.20 THEN 'TOP_20'
            ELSE 'STANDARD'
        END AS priority_bucket
    FROM infrastructure_details i
    JOIN schools s ON i.school_id = s.school_id
    WHERE i.risk_score IS NOT NULL
      AND i.academic_year = :year
""")

# ── Persistent high-risk flag: 3+ consecutive HIGH/CRITICAL years ────────────
# Uses a derived table with LAG to check previous two years' risk levels.

PERSISTENT_FLAG_SQL = text("""
    UPDATE school_priority_index p
    JOIN (
        SELECT
            school_id,
            academic_year,
            CASE
                WHEN risk_level IN ('HIGH', 'CRITICAL')
                 AND prev1_level IN ('HIGH', 'CRITICAL')
                 AND prev2_level IN ('HIGH', 'CRITICAL')
                THEN 1
                ELSE 0
            END AS flag
        FROM (
            SELECT
                i.school_id,
                i.academic_year,
                i.risk_level,
                LAG(i.risk_level, 1) OVER (
                    PARTITION BY i.school_id ORDER BY i.academic_year
                ) AS prev1_level,
                LAG(i.risk_level, 2) OVER (
                    PARTITION BY i.school_id ORDER BY i.academic_year
                ) AS prev2_level
            FROM infrastructure_details i
        ) sub
    ) derived
        ON  p.school_id     = derived.school_id
        AND p.academic_year  = derived.academic_year
    SET p.persistent_high_risk_flag = derived.flag
    WHERE p.academic_year = :year
""")

# ── Distinct years ───────────────────────────────────────────────────────────

YEARS_SQL = text("""
    SELECT DISTINCT academic_year
    FROM infrastructure_details
    WHERE risk_score IS NOT NULL
    ORDER BY academic_year
""")

# ── Summary queries ──────────────────────────────────────────────────────────

STATS_SQL = text("""
    SELECT
        COUNT(*)                                          AS total_records,
        SUM(CASE WHEN priority_bucket = 'TOP_5'    THEN 1 ELSE 0 END) AS top5,
        SUM(CASE WHEN priority_bucket = 'TOP_10'   THEN 1 ELSE 0 END) AS top10,
        SUM(CASE WHEN priority_bucket = 'TOP_20'   THEN 1 ELSE 0 END) AS top20,
        SUM(CASE WHEN priority_bucket = 'STANDARD' THEN 1 ELSE 0 END) AS standard,
        SUM(persistent_high_risk_flag)                    AS persistent_count
    FROM school_priority_index
""")

TOP_DISTRICTS_SQL = text("""
    SELECT
        s.district,
        COUNT(*)                                AS school_years,
        SUM(CASE WHEN p.priority_bucket IN ('TOP_5','TOP_10') THEN 1 ELSE 0 END)
            AS high_priority_count,
        SUM(p.persistent_high_risk_flag)        AS persistent_count
    FROM school_priority_index p
    JOIN schools s ON p.school_id = s.school_id
    GROUP BY s.district
    ORDER BY high_priority_count DESC
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
    print("Step 1/5 — Ensuring school_priority_index table exists...")
    with engine.begin() as conn:
        conn.execute(CREATE_TABLE_SQL)
    print("  [OK] Table ready.\n")

    # ── Step 2: Indexes ──────────────────────────────────────────────────
    print("Step 2/5 — Ensuring indexes...")
    with engine.begin() as conn:
        for name, ddl in INDEX_STATEMENTS:
            try:
                conn.execute(text(ddl))
                print(f"  [OK] Index '{name}' created.")
            except Exception:
                print(f"  [OK] Index '{name}' already exists.")
    print()

    # ── Step 3: Clear + repopulate (idempotent) ──────────────────────────
    print("Step 3/5 — Clearing existing data (idempotent reset)...")
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM school_priority_index"))
    print("  [OK] Cleared.\n")

    with engine.connect() as conn:
        years = [r["academic_year"] for r in conn.execute(YEARS_SQL).mappings().all()]

    print("Step 4/5 — Computing ranks & buckets (batched per year)...")
    t0 = time.time()
    total = 0
    for yr in years:
        t_yr = time.time()
        with engine.begin() as conn:
            result = conn.execute(POPULATE_SQL, {"year": yr})
            affected = result.rowcount
            total += affected
        print(f"  [OK] {yr}: {affected:,} rows  ({time.time() - t_yr:.1f}s)")
    print(f"\n  Ranks populated: {total:,} rows in {time.time() - t0:.1f}s.\n")

    # ── Step 4b: Persistent high-risk flag ───────────────────────────────
    print("Step 5/5 — Computing persistent high-risk flags...")
    t0 = time.time()
    total_flag = 0
    for yr in years:
        t_yr = time.time()
        with engine.begin() as conn:
            result = conn.execute(PERSISTENT_FLAG_SQL, {"year": yr})
            total_flag += result.rowcount
        print(f"  [OK] {yr}: ({time.time() - t_yr:.1f}s)")
    print(f"\n  Flags computed in {time.time() - t0:.1f}s.\n")

    # ── Summary ──────────────────────────────────────────────────────────
    print("Generating summary...")
    with engine.connect() as conn:
        stats = conn.execute(STATS_SQL).mappings().first()
        top_districts = conn.execute(TOP_DISTRICTS_SQL).mappings().all()

    sep = "=" * 56
    dash = "-" * 48
    lines = [
        "", sep,
        "School Prioritisation Engine — Summary",
        sep,
        f"Total school-year records  : {int(stats['total_records']):,}",
        f"  Top 5%    : {int(stats['top5']):>7,}",
        f"  Top 10%   : {int(stats['top10']):>7,}",
        f"  Top 20%   : {int(stats['top20']):>7,}",
        f"  Standard  : {int(stats['standard']):>7,}",
        f"  Persistent high-risk     : {int(stats['persistent_count']):,}",
        "",
        "Top 10 Districts by High-Priority Count:",
        dash,
    ]
    seen = set()
    for d in top_districts:
        district = str(d["district"] or "").strip()
        if not district or district in seen:
            continue
        seen.add(district)
        lines.append(
            f"{district:25s} priority: {int(d['high_priority_count']):>5,}"
            f"  persistent: {int(d['persistent_count']):>4,}"
        )
    lines.append(dash)
    print("\n".join(lines))


if __name__ == "__main__":
    print("=" * 56)
    print("  School AI BAV — Prioritisation Engine (v1.0)")
    print("=" * 56 + "\n")
    run()
