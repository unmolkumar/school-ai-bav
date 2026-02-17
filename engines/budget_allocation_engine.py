"""
budget_allocation_engine.py

Phase 6 — Budget Allocation Simulator (Bulk SQL)

Simulates resource allocation of classroom construction budget and
teacher posts, distributing in priority order (CRITICAL → HIGH →
MODERATE → LOW) until resources are exhausted.

Creates and populates the budget_simulation table with per-school-year
allocation results including classrooms_allocated, teachers_allocated,
and resolution status.

All computation runs server-side. No Python row loops for data
processing. Idempotent — safe to re-run.
"""

import os
import sys
import time

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ── Configuration (can be overridden via function params) ────────────────────

DEFAULT_CLASSROOM_BUDGET = 500_000_000   # ₹50 crore
DEFAULT_COST_PER_CLASSROOM = 500_000     # ₹5 lakh per classroom
DEFAULT_TEACHER_POSTS = 10_000           # total posts available

# ── Table DDL ────────────────────────────────────────────────────────────────

CREATE_TABLE_SQL = text("""
    CREATE TABLE IF NOT EXISTS budget_simulation (
        id                    INT AUTO_INCREMENT PRIMARY KEY,
        school_id             VARCHAR(50)  NOT NULL,
        academic_year         VARCHAR(20)  NOT NULL,
        risk_level            VARCHAR(20),
        classroom_gap         INT DEFAULT 0,
        teacher_gap           INT DEFAULT 0,
        classrooms_allocated  INT DEFAULT 0,
        teachers_allocated    INT DEFAULT 0,
        classroom_resolved    TINYINT DEFAULT 0,
        teacher_resolved      TINYINT DEFAULT 0,
        allocation_priority   INT
    )
""")

INDEX_STATEMENTS = [
    (
        "idx_budget_school_year",
        "CREATE INDEX idx_budget_school_year "
        "ON budget_simulation (school_id, academic_year)"
    ),
    (
        "idx_budget_priority",
        "CREATE INDEX idx_budget_priority "
        "ON budget_simulation (academic_year, allocation_priority)"
    ),
]

# ── Populate: seed from existing gap data ────────────────────────────────────

SEED_SQL = text("""
    INSERT INTO budget_simulation
        (school_id, academic_year, risk_level, classroom_gap,
         teacher_gap, allocation_priority)
    SELECT
        i.school_id,
        i.academic_year,
        i.risk_level,
        IFNULL(i.classroom_gap, 0),
        IFNULL(t.teacher_gap, 0),
        ROW_NUMBER() OVER (
            ORDER BY
                CASE i.risk_level
                    WHEN 'CRITICAL' THEN 1
                    WHEN 'HIGH'     THEN 2
                    WHEN 'MODERATE' THEN 3
                    WHEN 'LOW'      THEN 4
                    ELSE 5
                END,
                i.risk_score DESC
        ) AS allocation_priority
    FROM infrastructure_details i
    JOIN teacher_metrics t
        ON  i.school_id     = t.school_id
        AND i.academic_year  = t.academic_year
    WHERE i.risk_score IS NOT NULL
      AND i.academic_year = :year
""")

# ── Allocation: cumulative sum approach ──────────────────────────────────────
# Uses a derived table with running totals to determine cutoff.

ALLOCATE_CLASSROOMS_SQL = text("""
    UPDATE budget_simulation b
    JOIN (
        SELECT
            id,
            classroom_gap,
            SUM(classroom_gap) OVER (
                ORDER BY allocation_priority
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS running_total
        FROM budget_simulation
        WHERE academic_year = :year
    ) cum ON b.id = cum.id
    SET
        b.classrooms_allocated = CASE
            WHEN cum.running_total <= :max_classrooms THEN b.classroom_gap
            WHEN (cum.running_total - b.classroom_gap) < :max_classrooms
                THEN :max_classrooms - (cum.running_total - b.classroom_gap)
            ELSE 0
        END,
        b.classroom_resolved = CASE
            WHEN cum.running_total <= :max_classrooms THEN 1
            ELSE 0
        END
    WHERE b.academic_year = :year
""")

ALLOCATE_TEACHERS_SQL = text("""
    UPDATE budget_simulation b
    JOIN (
        SELECT
            id,
            teacher_gap,
            SUM(teacher_gap) OVER (
                ORDER BY allocation_priority
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS running_total
        FROM budget_simulation
        WHERE academic_year = :year
    ) cum ON b.id = cum.id
    SET
        b.teachers_allocated = CASE
            WHEN cum.running_total <= :max_teachers THEN b.teacher_gap
            WHEN (cum.running_total - b.teacher_gap) < :max_teachers
                THEN :max_teachers - (cum.running_total - b.teacher_gap)
            ELSE 0
        END,
        b.teacher_resolved = CASE
            WHEN cum.running_total <= :max_teachers THEN 1
            ELSE 0
        END
    WHERE b.academic_year = :year
""")

# ── Summary queries ──────────────────────────────────────────────────────────

YEARS_SQL = text("""
    SELECT DISTINCT academic_year
    FROM infrastructure_details
    WHERE risk_score IS NOT NULL
    ORDER BY academic_year
""")

STATS_SQL = text("""
    SELECT
        COUNT(*)                            AS total_records,
        SUM(classrooms_allocated)           AS total_classrooms_alloc,
        SUM(teachers_allocated)             AS total_teachers_alloc,
        SUM(classroom_resolved)             AS schools_classroom_resolved,
        SUM(teacher_resolved)               AS schools_teacher_resolved,
        SUM(GREATEST(classroom_gap - classrooms_allocated, 0))
                                            AS remaining_classroom_deficit,
        SUM(GREATEST(teacher_gap - teachers_allocated, 0))
                                            AS remaining_teacher_deficit
    FROM budget_simulation
""")

DISTRICT_COVERAGE_SQL = text("""
    SELECT
        s.district,
        COUNT(*)                          AS school_years,
        SUM(b.classroom_resolved)         AS cr_resolved,
        ROUND(100.0 * SUM(b.classroom_resolved) / COUNT(*), 1)
                                          AS cr_coverage_pct,
        SUM(b.teacher_resolved)           AS tr_resolved,
        ROUND(100.0 * SUM(b.teacher_resolved) / COUNT(*), 1)
                                          AS tr_coverage_pct
    FROM budget_simulation b
    JOIN schools s ON b.school_id = s.school_id
    GROUP BY s.district
    ORDER BY cr_coverage_pct DESC
    LIMIT 10
""")


# ── Main engine ──────────────────────────────────────────────────────────────


def run(classroom_budget=DEFAULT_CLASSROOM_BUDGET,
        cost_per_classroom=DEFAULT_COST_PER_CLASSROOM,
        teacher_posts=DEFAULT_TEACHER_POSTS):

    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not found in .env")
        sys.exit(1)

    max_classrooms = classroom_budget // cost_per_classroom
    max_teachers = teacher_posts

    engine = create_engine(
        DATABASE_URL, echo=False,
        pool_recycle=280, pool_pre_ping=True,
        connect_args={"connect_timeout": 30},
    )

    # ── Step 1: Create table ─────────────────────────────────────────────
    print("Step 1/5 — Ensuring budget_simulation table exists...")
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

    # ── Step 3: Clear + seed ─────────────────────────────────────────────
    print("Step 3/5 — Seeding allocation data (idempotent reset)...")
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM budget_simulation"))

    with engine.connect() as conn:
        years = [r["academic_year"] for r in conn.execute(YEARS_SQL).mappings().all()]

    t0 = time.time()
    total = 0
    for yr in years:
        t_yr = time.time()
        with engine.begin() as conn:
            result = conn.execute(SEED_SQL, {"year": yr})
            total += result.rowcount
        print(f"  [OK] {yr}: seeded  ({time.time() - t_yr:.1f}s)")
    print(f"\n  Seeded: {total:,} rows in {time.time() - t0:.1f}s.\n")

    # ── Step 4: Allocate resources ───────────────────────────────────────
    print(f"Step 4/5 — Allocating resources (per year)...")
    print(f"  Budget: {max_classrooms:,} classrooms, {max_teachers:,} teacher posts\n")
    t0 = time.time()
    for yr in years:
        t_yr = time.time()
        with engine.begin() as conn:
            conn.execute(ALLOCATE_CLASSROOMS_SQL, {
                "year": yr, "max_classrooms": max_classrooms
            })
            conn.execute(ALLOCATE_TEACHERS_SQL, {
                "year": yr, "max_teachers": max_teachers
            })
        print(f"  [OK] {yr}: allocated  ({time.time() - t_yr:.1f}s)")
    print(f"\n  Allocation completed in {time.time() - t0:.1f}s.\n")

    # ── Step 5: Summary ──────────────────────────────────────────────────
    print("Step 5/5 — Generating summary...")
    with engine.connect() as conn:
        stats = conn.execute(STATS_SQL).mappings().first()
        districts = conn.execute(DISTRICT_COVERAGE_SQL).mappings().all()

    sep = "=" * 60
    dash = "-" * 52
    lines = [
        "", sep,
        "Budget Allocation Simulator — Summary",
        sep,
        f"Simulation parameters:",
        f"  Classroom budget       : Rs {classroom_budget:,}",
        f"  Cost per classroom     : Rs {cost_per_classroom:,}",
        f"  Max classrooms         : {max_classrooms:,}",
        f"  Teacher posts available : {max_teachers:,}",
        "",
        f"Total school-year records    : {int(stats['total_records']):,}",
        f"Classrooms allocated         : {int(stats['total_classrooms_alloc']):,}",
        f"Teachers allocated           : {int(stats['total_teachers_alloc']):,}",
        f"Schools classroom-resolved   : {int(stats['schools_classroom_resolved']):,}",
        f"Schools teacher-resolved     : {int(stats['schools_teacher_resolved']):,}",
        f"Remaining classroom deficit  : {int(stats['remaining_classroom_deficit']):,}",
        f"Remaining teacher deficit    : {int(stats['remaining_teacher_deficit']):,}",
        "",
        "Top 10 Districts by Classroom Coverage:",
        dash,
    ]
    seen = set()
    for d in districts:
        district = str(d["district"] or "").strip()
        if not district or district in seen:
            continue
        seen.add(district)
        lines.append(
            f"{district:22s} CR: {float(d['cr_coverage_pct']):>5.1f}%"
            f"  TR: {float(d['tr_coverage_pct']):>5.1f}%"
        )
    lines.append(dash)
    print("\n".join(lines))


if __name__ == "__main__":
    print("=" * 60)
    print("  School AI BAV — Budget Allocation Simulator (v1.0)")
    print("=" * 60 + "\n")
    run()
