"""
risk_trend_engine.py

Phase 7 — Longitudinal Risk Trend Engine (Bulk SQL)

Tracks how each school's risk_score changes over time.
Computes risk deltas, classifies trend direction, identifies
chronic high-risk and volatile schools across multi-year data.

Creates and populates the risk_trend table:
  - risk_delta           : current risk_score − previous year's (via LAG)
  - trend_direction      : IMPROVING / STABLE / DETERIORATING
  - year_over_year_count : which sequential year this is for the school
  - chronic_risk_flag    : 1 if school has been HIGH/CRITICAL for 3+ consecutive years
  - volatile_flag        : 1 if |risk_delta| > 0.25 in any of last 2 transitions
  - cumulative_avg_risk  : running average of risk_score across all years

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
    CREATE TABLE IF NOT EXISTS risk_trend (
        id                    INT AUTO_INCREMENT PRIMARY KEY,
        school_id             VARCHAR(50)  NOT NULL,
        academic_year         VARCHAR(20)  NOT NULL,
        risk_score            FLOAT,
        prev_risk_score       FLOAT,
        risk_delta            FLOAT,
        trend_direction       VARCHAR(20),
        year_over_year_count  INT,
        chronic_risk_flag     TINYINT DEFAULT 0,
        volatile_flag         TINYINT DEFAULT 0,
        cumulative_avg_risk   FLOAT
    )
""")

# ── Index ────────────────────────────────────────────────────────────────────

INDEX_STATEMENTS = [
    (
        "idx_trend_school_year",
        "CREATE INDEX idx_trend_school_year "
        "ON risk_trend (school_id, academic_year)"
    ),
    (
        "idx_trend_direction",
        "CREATE INDEX idx_trend_direction "
        "ON risk_trend (academic_year, trend_direction)"
    ),
]

# ── Core INSERT: risk_delta + trend + cumulative avg via window functions ───

POPULATE_SQL = text("""
    INSERT INTO risk_trend
        (school_id, academic_year, risk_score, prev_risk_score,
         risk_delta, trend_direction, year_over_year_count,
         cumulative_avg_risk)
    SELECT
        sub.school_id,
        sub.academic_year,
        sub.risk_score,
        sub.prev_risk_score,
        sub.risk_delta,
        CASE
            WHEN sub.risk_delta IS NULL THEN 'BASELINE'
            WHEN sub.risk_delta < -0.10 THEN 'IMPROVING'
            WHEN sub.risk_delta >  0.10 THEN 'DETERIORATING'
            ELSE 'STABLE'
        END AS trend_direction,
        sub.yr_seq,
        sub.cum_avg
    FROM (
        SELECT
            i.school_id,
            i.academic_year,
            i.risk_score,
            LAG(i.risk_score, 1) OVER (
                PARTITION BY i.school_id ORDER BY i.academic_year
            ) AS prev_risk_score,
            i.risk_score - LAG(i.risk_score, 1) OVER (
                PARTITION BY i.school_id ORDER BY i.academic_year
            ) AS risk_delta,
            ROW_NUMBER() OVER (
                PARTITION BY i.school_id ORDER BY i.academic_year
            ) AS yr_seq,
            AVG(i.risk_score) OVER (
                PARTITION BY i.school_id
                ORDER BY i.academic_year
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS cum_avg
        FROM infrastructure_details i
        WHERE i.risk_score IS NOT NULL
          AND i.academic_year = :year
    ) sub
""")

# ── Chronic risk flag: 3+ consecutive years HIGH/CRITICAL ─────────────────
# Uses LAG to check previous 2 years from infrastructure_details (has risk_level)

CHRONIC_FLAG_SQL = text("""
    UPDATE risk_trend rt
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
        ON  rt.school_id     = derived.school_id
        AND rt.academic_year  = derived.academic_year
    SET rt.chronic_risk_flag = derived.flag
    WHERE rt.academic_year = :year
""")

# ── Volatile flag: |risk_delta| > 0.25 in current or previous transition ──

VOLATILE_FLAG_SQL = text("""
    UPDATE risk_trend rt
    JOIN (
        SELECT
            school_id,
            academic_year,
            CASE
                WHEN ABS(risk_delta) > 0.25
                  OR ABS(prev_delta) > 0.25
                THEN 1
                ELSE 0
            END AS flag
        FROM (
            SELECT
                school_id,
                academic_year,
                risk_delta,
                LAG(risk_delta, 1) OVER (
                    PARTITION BY school_id ORDER BY academic_year
                ) AS prev_delta
            FROM risk_trend
        ) sub
    ) derived
        ON  rt.school_id     = derived.school_id
        AND rt.academic_year  = derived.academic_year
    SET rt.volatile_flag = derived.flag
    WHERE rt.academic_year = :year
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
        COUNT(*)                                                        AS total,
        SUM(CASE WHEN trend_direction = 'BASELINE'      THEN 1 ELSE 0 END) AS baseline,
        SUM(CASE WHEN trend_direction = 'IMPROVING'     THEN 1 ELSE 0 END) AS improving,
        SUM(CASE WHEN trend_direction = 'STABLE'        THEN 1 ELSE 0 END) AS stable,
        SUM(CASE WHEN trend_direction = 'DETERIORATING' THEN 1 ELSE 0 END) AS deteriorating,
        SUM(chronic_risk_flag)                                          AS chronic,
        SUM(volatile_flag)                                              AS volatile,
        ROUND(AVG(cumulative_avg_risk), 4)                              AS mean_cum_avg
    FROM risk_trend
""")

DISTRICT_TREND_SQL = text("""
    SELECT
        s.district,
        COUNT(*)                                                        AS records,
        SUM(CASE WHEN rt.trend_direction = 'DETERIORATING' THEN 1 ELSE 0 END) AS deteriorating,
        SUM(rt.chronic_risk_flag)                                       AS chronic,
        SUM(rt.volatile_flag)                                           AS volatile,
        ROUND(AVG(rt.risk_delta), 4)                                    AS avg_delta
    FROM risk_trend rt
    JOIN schools s ON rt.school_id = s.school_id
    GROUP BY s.district
    ORDER BY deteriorating DESC
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
    print("Step 1/6 — Ensuring risk_trend table exists...")
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
        conn.execute(text("DELETE FROM risk_trend"))
    print("  [OK] Cleared.\n")

    # ── Step 4: Populate all years ───────────────────────────────────────
    # NOTE: We must INSERT all years first before computing volatile flag
    # because it needs LAG across the risk_trend table itself.
    # But risk_delta from LAG in the INSERT only sees data from infra table
    # which already has all years. So we do:
    #   4a. Insert all years (risk_delta + trend via infra LAG)
    #   4b. Chronic flag (needs infra LAG across years — works per year)
    #   4c. Volatile flag (needs risk_trend LAG — only after all rows exist)

    with engine.connect() as conn:
        years = [r["academic_year"] for r in conn.execute(YEARS_SQL).mappings().all()]

    print("Step 4/6 — Computing risk deltas & trends (batched per year)...")
    t0 = time.time()
    total = 0

    # For the POPULATE_SQL, LAG needs to see all years in infra (which it does),
    # but we filter INSERT by year. This is fine because the LAG window is over
    # the full partition (not filtered by WHERE on outer SELECT since the
    # window is in the subquery). Actually, the WHERE is inside the subquery
    # so LAG won't have previous years. We need to restructure.

    # Better approach: INSERT all at once without year filter for correct LAG,
    # but that is one big INSERT. Let's do it year-independent.

    # Actually, let's restructure: remove year filter from subquery so LAG
    # works correctly, then INSERT all rows at once.

    # Since we need correct LAG, we'll insert all years in one pass.
    print("  Computing full longitudinal window...")
    t_all = time.time()
    with engine.begin() as conn:
        result = conn.execute(text("""
            INSERT INTO risk_trend
                (school_id, academic_year, risk_score, prev_risk_score,
                 risk_delta, trend_direction, year_over_year_count,
                 cumulative_avg_risk)
            SELECT
                sub.school_id,
                sub.academic_year,
                sub.risk_score,
                sub.prev_risk_score,
                sub.risk_delta,
                CASE
                    WHEN sub.risk_delta IS NULL THEN 'BASELINE'
                    WHEN sub.risk_delta < -0.10 THEN 'IMPROVING'
                    WHEN sub.risk_delta >  0.10 THEN 'DETERIORATING'
                    ELSE 'STABLE'
                END AS trend_direction,
                sub.yr_seq,
                sub.cum_avg
            FROM (
                SELECT
                    i.school_id,
                    i.academic_year,
                    i.risk_score,
                    LAG(i.risk_score, 1) OVER (
                        PARTITION BY i.school_id ORDER BY i.academic_year
                    ) AS prev_risk_score,
                    i.risk_score - LAG(i.risk_score, 1) OVER (
                        PARTITION BY i.school_id ORDER BY i.academic_year
                    ) AS risk_delta,
                    ROW_NUMBER() OVER (
                        PARTITION BY i.school_id ORDER BY i.academic_year
                    ) AS yr_seq,
                    AVG(i.risk_score) OVER (
                        PARTITION BY i.school_id
                        ORDER BY i.academic_year
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    ) AS cum_avg
                FROM infrastructure_details i
                WHERE i.risk_score IS NOT NULL
            ) sub
        """))
        total = result.rowcount
    print(f"  [OK] {total:,} rows inserted  ({time.time() - t_all:.1f}s)\n")

    # ── Step 5: Chronic risk flag ────────────────────────────────────────
    print("Step 5/6 — Computing chronic risk flags (batched per year)...")
    t0 = time.time()
    for yr in years:
        t_yr = time.time()
        with engine.begin() as conn:
            conn.execute(CHRONIC_FLAG_SQL, {"year": yr})
        print(f"  [OK] {yr}: ({time.time() - t_yr:.1f}s)")
    print(f"\n  Chronic flags computed in {time.time() - t0:.1f}s.\n")

    # ── Step 6: Volatile flag ────────────────────────────────────────────
    print("Step 6/6 — Computing volatile flags (batched per year)...")
    t0 = time.time()
    for yr in years:
        t_yr = time.time()
        with engine.begin() as conn:
            conn.execute(VOLATILE_FLAG_SQL, {"year": yr})
        print(f"  [OK] {yr}: ({time.time() - t_yr:.1f}s)")
    print(f"\n  Volatile flags computed in {time.time() - t0:.1f}s.\n")

    # ── Summary ──────────────────────────────────────────────────────────
    print("Generating summary...")
    with engine.connect() as conn:
        stats = conn.execute(STATS_SQL).mappings().first()
        districts = conn.execute(DISTRICT_TREND_SQL).mappings().all()

    sep = "=" * 60
    dash = "-" * 56
    lines = [
        "", sep,
        "Longitudinal Risk Trend Engine — Summary",
        sep,
        f"Total school-year records : {int(stats['total']):,}",
        f"  BASELINE      : {int(stats['baseline']):>7,}  (first year — no prior data)",
        f"  IMPROVING     : {int(stats['improving']):>7,}  (delta < -0.10)",
        f"  STABLE        : {int(stats['stable']):>7,}  (|delta| <= 0.10)",
        f"  DETERIORATING : {int(stats['deteriorating']):>7,}  (delta > +0.10)",
        f"  Chronic risk  : {int(stats['chronic']):>7,}  (3+ consec HIGH/CRITICAL)",
        f"  Volatile      : {int(stats['volatile']):>7,}  (|delta| > 0.25 recent)",
        f"  Mean cumulative avg risk: {stats['mean_cum_avg']}",
        "",
        "Top 10 Districts by Deteriorating Count:",
        dash,
    ]
    for d in districts:
        district = str(d["district"] or "").strip()
        lines.append(
            f"  {district:22s}  detr: {int(d['deteriorating']):>5,}"
            f"  chronic: {int(d['chronic']):>4,}"
            f"  volatile: {int(d['volatile']):>4,}"
            f"  avg_delta: {d['avg_delta']}"
        )
    lines.append(dash)
    print("\n".join(lines))


if __name__ == "__main__":
    print("=" * 60)
    print("  School AI BAV — Risk Trend Engine (v1.0)")
    print("=" * 60 + "\n")
    run()
