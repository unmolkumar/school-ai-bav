"""
forecasting_engine.py

Phase 10 — Enrolment Forecasting Engine (Bulk SQL)

Projects future enrolment, classroom requirements, and teacher
requirements for each school using moving-average trend computation.

Approach:
  1. Compute YoY enrolment growth rate per school (via LAG).
  2. Calculate weighted moving average growth (3-year window).
  3. Project 3 years forward (Year+1, Year+2, Year+3)
     from the latest available year.
  4. Derive projected classroom and teacher requirements
     using UDISE+ norms (school_category based PTR/room size).
  5. Compute projected deficits against current capacity.

Creates and populates:
  - enrolment_forecast : projected enrolment + requirements for T+1..T+3

All computation runs server-side via window functions + CASE.
No Python row loops. Idempotent — safe to re-run.
"""

import os
import sys
import time

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ── Table DDL ────────────────────────────────────────────────────────────────

CREATE_TABLE_SQL = text("""
    CREATE TABLE IF NOT EXISTS enrolment_forecast (
        id                         INT AUTO_INCREMENT PRIMARY KEY,
        school_id                  VARCHAR(50)  NOT NULL,
        base_year                  VARCHAR(20)  NOT NULL,
        forecast_year              VARCHAR(20)  NOT NULL,
        years_ahead                INT,
        base_enrolment             INT,
        avg_growth_rate            FLOAT,
        projected_enrolment        INT,
        projected_classrooms_req   INT,
        projected_teachers_req     INT,
        current_classrooms         INT,
        current_teachers           INT,
        projected_classroom_gap    INT,
        projected_teacher_gap      INT,
        school_category            INT
    )
""")

# ── Indexes ──────────────────────────────────────────────────────────────────

INDEX_STATEMENTS = [
    (
        "idx_forecast_school",
        "CREATE INDEX idx_forecast_school "
        "ON enrolment_forecast (school_id, base_year)"
    ),
    (
        "idx_forecast_year",
        "CREATE INDEX idx_forecast_year "
        "ON enrolment_forecast (forecast_year, years_ahead)"
    ),
]

# ── Core INSERT: project from latest year data ──────────────────────────────
# Generates 3 forecast rows per school (T+1, T+2, T+3).
# Growth rate is weighted moving average of last 3 years' YoY growth.
# Classroom norm: category 1-3 → 30, 4-5 → 35, 6-11 → 40
# PTR norm: category 1-5 → 30, 6-11 → 35

FORECAST_SQL = text("""
    INSERT INTO enrolment_forecast
        (school_id, base_year, forecast_year, years_ahead,
         base_enrolment, avg_growth_rate, projected_enrolment,
         projected_classrooms_req, projected_teachers_req,
         current_classrooms, current_teachers,
         projected_classroom_gap, projected_teacher_gap,
         school_category)
    SELECT
        f.school_id,
        f.base_year,
        CONCAT(
            CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(f.base_year, '-', 1), '-', -1) AS UNSIGNED)
                + f.years_ahead,
            '-',
            LPAD(
                (CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(f.base_year, '-', -1), '-', 1) AS UNSIGNED)
                    + f.years_ahead),
                2, '0'
            )
        ) AS forecast_year,
        f.years_ahead,
        f.base_enrolment,
        f.avg_growth_rate,
        -- Projected enrolment = base * (1 + growth)^years_ahead
        -- Cap growth at -0.30 to +0.30 to avoid wild projections
        GREATEST(0, ROUND(
            f.base_enrolment * POW(
                1 + LEAST(0.30, GREATEST(-0.30, f.avg_growth_rate)),
                f.years_ahead
            )
        )) AS projected_enrolment,
        -- Projected classroom requirement
        CEILING(
            GREATEST(0, ROUND(
                f.base_enrolment * POW(
                    1 + LEAST(0.30, GREATEST(-0.30, f.avg_growth_rate)),
                    f.years_ahead
                )
            ))
            / f.classroom_norm
        ) AS projected_classrooms_req,
        -- Projected teacher requirement
        CEILING(
            GREATEST(0, ROUND(
                f.base_enrolment * POW(
                    1 + LEAST(0.30, GREATEST(-0.30, f.avg_growth_rate)),
                    f.years_ahead
                )
            ))
            / f.ptr_norm
        ) AS projected_teachers_req,
        f.current_classrooms,
        f.current_teachers,
        -- Projected classroom gap (positive = deficit)
        GREATEST(0,
            CEILING(
                GREATEST(0, ROUND(
                    f.base_enrolment * POW(
                        1 + LEAST(0.30, GREATEST(-0.30, f.avg_growth_rate)),
                        f.years_ahead
                    )
                ))
                / f.classroom_norm
            ) - f.current_classrooms
        ),
        -- Projected teacher gap
        GREATEST(0,
            CEILING(
                GREATEST(0, ROUND(
                    f.base_enrolment * POW(
                        1 + LEAST(0.30, GREATEST(-0.30, f.avg_growth_rate)),
                        f.years_ahead
                    )
                ))
                / f.ptr_norm
            ) - f.current_teachers
        ),
        f.school_category
    FROM (
        SELECT
            base.school_id,
            base.base_year,
            base.base_enrolment,
            base.avg_growth_rate,
            base.current_classrooms,
            base.current_teachers,
            base.school_category,
            -- Classroom norm by school_category
            CASE
                WHEN base.school_category IN (1, 2, 3)     THEN 30
                WHEN base.school_category IN (4, 5)         THEN 35
                ELSE 40
            END AS classroom_norm,
            -- PTR norm by school_category
            CASE
                WHEN base.school_category IN (1, 2, 3, 4, 5) THEN 30
                ELSE 35
            END AS ptr_norm,
            gen.years_ahead
        FROM (
            SELECT
                growth_sub.school_id,
                growth_sub.academic_year                     AS base_year,
                growth_sub.total_enrolment                   AS base_enrolment,
                growth_sub.avg_growth_rate,
                IFNULL(i.usable_class_rooms, 0)              AS current_classrooms,
                IFNULL(t.total_teachers, 0)                   AS current_teachers,
                IFNULL(s.school_category, 6)                  AS school_category
            FROM (
                -- Subquery computes LAG over ALL years then filters
                SELECT
                    y.school_id,
                    y.academic_year,
                    y.total_enrolment,
                    IFNULL(
                        (
                            IFNULL(y.total_enrolment - LAG(y.total_enrolment, 1) OVER (
                                PARTITION BY y.school_id ORDER BY y.academic_year
                            ), 0) * 3.0
                            +
                            IFNULL(
                                LAG(y.total_enrolment, 1) OVER (
                                    PARTITION BY y.school_id ORDER BY y.academic_year
                                ) - LAG(y.total_enrolment, 2) OVER (
                                    PARTITION BY y.school_id ORDER BY y.academic_year
                                ), 0) * 2.0
                            +
                            IFNULL(
                                LAG(y.total_enrolment, 2) OVER (
                                    PARTITION BY y.school_id ORDER BY y.academic_year
                                ) - LAG(y.total_enrolment, 3) OVER (
                                    PARTITION BY y.school_id ORDER BY y.academic_year
                                ), 0) * 1.0
                        ) / NULLIF(
                            (3.0 + 2.0 + 1.0) * LAG(y.total_enrolment, 1) OVER (
                                PARTITION BY y.school_id ORDER BY y.academic_year
                            ), 0),
                        0
                    ) AS avg_growth_rate
                FROM yearly_metrics y
            ) growth_sub
            JOIN schools s ON growth_sub.school_id = s.school_id
            LEFT JOIN infrastructure_details i
                ON growth_sub.school_id = i.school_id
                AND growth_sub.academic_year = i.academic_year
            LEFT JOIN teacher_metrics t
                ON growth_sub.school_id = t.school_id
                AND growth_sub.academic_year = t.academic_year
            WHERE growth_sub.academic_year = :year
        ) base
        -- Cross join with (1,2,3) to generate 3 forecast rows per school
        CROSS JOIN (
            SELECT 1 AS years_ahead
            UNION ALL SELECT 2
            UNION ALL SELECT 3
        ) gen
    ) f
""")

# ── Distinct years ───────────────────────────────────────────────────────────

LATEST_YEAR_SQL = text("""
    SELECT MAX(academic_year) AS latest_year
    FROM yearly_metrics
""")

# ── Summary ──────────────────────────────────────────────────────────────────

STATS_SQL = text("""
    SELECT
        COUNT(*)                          AS total_records,
        COUNT(DISTINCT school_id)         AS unique_schools,
        base_year,
        MIN(forecast_year)                AS first_forecast,
        MAX(forecast_year)                AS last_forecast,
        ROUND(AVG(avg_growth_rate), 4)    AS mean_growth,
        ROUND(AVG(projected_enrolment), 0) AS avg_proj_enrolment,
        SUM(projected_classroom_gap)      AS total_proj_cr_gap,
        SUM(projected_teacher_gap)        AS total_proj_tr_gap,
        SUM(CASE WHEN years_ahead = 1 THEN projected_classroom_gap ELSE 0 END) AS yr1_cr_gap,
        SUM(CASE WHEN years_ahead = 2 THEN projected_classroom_gap ELSE 0 END) AS yr2_cr_gap,
        SUM(CASE WHEN years_ahead = 3 THEN projected_classroom_gap ELSE 0 END) AS yr3_cr_gap,
        SUM(CASE WHEN years_ahead = 1 THEN projected_teacher_gap ELSE 0 END)   AS yr1_tr_gap,
        SUM(CASE WHEN years_ahead = 2 THEN projected_teacher_gap ELSE 0 END)   AS yr2_tr_gap,
        SUM(CASE WHEN years_ahead = 3 THEN projected_teacher_gap ELSE 0 END)   AS yr3_tr_gap
    FROM enrolment_forecast
    GROUP BY base_year
""")

DISTRICT_FORECAST_SQL = text("""
    SELECT
        s.district,
        SUM(ef.projected_enrolment)     AS total_proj_enrolment,
        SUM(ef.projected_classroom_gap) AS total_proj_cr_gap,
        SUM(ef.projected_teacher_gap)   AS total_proj_tr_gap,
        ROUND(AVG(ef.avg_growth_rate), 4) AS avg_growth
    FROM enrolment_forecast ef
    JOIN schools s ON ef.school_id = s.school_id
    WHERE ef.years_ahead = 3
    GROUP BY s.district
    ORDER BY total_proj_cr_gap DESC
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
    print("Step 1/5 — Ensuring enrolment_forecast table exists...")
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

    # ── Step 3: Clear ────────────────────────────────────────────────────
    print("Step 3/5 — Clearing existing data (idempotent reset)...")
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM enrolment_forecast"))
    print("  [OK] Cleared.\n")

    # ── Step 4: Forecast from latest year ────────────────────────────────
    with engine.connect() as conn:
        latest = conn.execute(LATEST_YEAR_SQL).mappings().first()["latest_year"]
    print(f"Step 4/5 — Generating 3-year forecast from base year {latest}...")

    t0 = time.time()
    with engine.begin() as conn:
        result = conn.execute(FORECAST_SQL, {"year": latest})
        total = result.rowcount
    print(f"  [OK] {total:,} forecast rows generated  ({time.time() - t0:.1f}s)\n")

    # ── Step 5: Summary ──────────────────────────────────────────────────
    print("Step 5/5 — Generating summary...")
    with engine.connect() as conn:
        stats = conn.execute(STATS_SQL).mappings().first()
        districts = conn.execute(DISTRICT_FORECAST_SQL).mappings().all()

    sep = "=" * 62
    dash = "-" * 58
    lines = [
        "", sep,
        "Enrolment Forecasting Engine — Summary",
        sep,
        f"Base year                  : {stats['base_year']}",
        f"Forecast range             : {stats['first_forecast']} → {stats['last_forecast']}",
        f"Unique schools             : {int(stats['unique_schools']):,}",
        f"Total forecast records     : {int(stats['total_records']):,}",
        f"Mean growth rate            : {stats['mean_growth']}",
        f"Avg projected enrolment    : {int(stats['avg_proj_enrolment']):,}",
        "",
        "Projected Classroom Deficit by Horizon:",
        f"  T+1 : {int(stats['yr1_cr_gap']):>10,}",
        f"  T+2 : {int(stats['yr2_cr_gap']):>10,}",
        f"  T+3 : {int(stats['yr3_cr_gap']):>10,}",
        "",
        "Projected Teacher Deficit by Horizon:",
        f"  T+1 : {int(stats['yr1_tr_gap']):>10,}",
        f"  T+2 : {int(stats['yr2_tr_gap']):>10,}",
        f"  T+3 : {int(stats['yr3_tr_gap']):>10,}",
        "",
        "Top 10 Districts by T+3 Classroom Deficit:",
        dash,
    ]
    for d in districts:
        district = str(d["district"] or "").strip()
        lines.append(
            f"  {district:22s}"
            f"  enrl: {int(d['total_proj_enrolment']):>9,}"
            f"  cr_gap: {int(d['total_proj_cr_gap']):>6,}"
            f"  tr_gap: {int(d['total_proj_tr_gap']):>6,}"
            f"  growth: {d['avg_growth']}"
        )
    lines.append(dash)
    print("\n".join(lines))


if __name__ == "__main__":
    print("=" * 62)
    print("  School AI BAV — Forecasting Engine (v1.0)")
    print("=" * 62 + "\n")
    run()
