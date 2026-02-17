"""
proposal_validation_engine.py

Phase 9 — Proposal Validation Engine (Bulk SQL)

Simulates validation of school-level demand proposals (classroom and
teacher requests) against actual computed gaps from Phases 2-4.

Workflow:
  1. Generates synthetic demand proposals from existing gap data
     (with noise to simulate real-world over/under-requesting).
  2. Validates each proposal against computed gaps.
  3. Assigns decision: ACCEPTED / FLAGGED / REJECTED.
  4. Computes confidence_score and reason_code.

Creates and populates:
  - school_demand_proposals : simulated proposal input
  - proposal_validations    : validated output with decision + confidence

All computation runs server-side via SQL CASE + JOINs.
No Python row loops. Idempotent — safe to re-run.
"""

import os
import sys
import time

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ── Table DDL ────────────────────────────────────────────────────────────────

CREATE_PROPOSALS_SQL = text("""
    CREATE TABLE IF NOT EXISTS school_demand_proposals (
        id                    INT AUTO_INCREMENT PRIMARY KEY,
        school_id             VARCHAR(50)  NOT NULL,
        academic_year         VARCHAR(20)  NOT NULL,
        requested_classrooms  INT          DEFAULT 0,
        requested_teachers    INT          DEFAULT 0,
        proposal_source       VARCHAR(30)  DEFAULT 'SIMULATION'
    )
""")

CREATE_VALIDATIONS_SQL = text("""
    CREATE TABLE IF NOT EXISTS proposal_validations (
        id                    INT AUTO_INCREMENT PRIMARY KEY,
        school_id             VARCHAR(50)  NOT NULL,
        academic_year         VARCHAR(20)  NOT NULL,
        requested_classrooms  INT,
        requested_teachers    INT,
        actual_classroom_gap  INT,
        actual_teacher_gap    INT,
        classroom_ratio       FLOAT,
        teacher_ratio         FLOAT,
        decision_status       VARCHAR(20),
        reason_code           VARCHAR(50),
        confidence_score      FLOAT
    )
""")

# ── Indexes ──────────────────────────────────────────────────────────────────

INDEX_STATEMENTS = [
    (
        "idx_proposals_school_year",
        "CREATE INDEX idx_proposals_school_year "
        "ON school_demand_proposals (school_id, academic_year)"
    ),
    (
        "idx_validations_school_year",
        "CREATE INDEX idx_validations_school_year "
        "ON proposal_validations (school_id, academic_year)"
    ),
    (
        "idx_validations_decision",
        "CREATE INDEX idx_validations_decision "
        "ON proposal_validations (academic_year, decision_status)"
    ),
]

# ── Seed synthetic proposals from actual gaps (with noise) ───────────────────
# Adds ±30% noise to simulate realistic over/under-requesting.
# Uses deterministic noise based on school_id hash for reproducibility.

SEED_PROPOSALS_SQL = text("""
    INSERT INTO school_demand_proposals
        (school_id, academic_year, requested_classrooms, requested_teachers,
         proposal_source)
    SELECT
        i.school_id,
        i.academic_year,
        -- Classroom request: actual gap × (0.7 to 1.5) noise factor
        -- CRC32 gives deterministic pseudo-random based on school_id
        GREATEST(0, ROUND(
            CASE WHEN i.classroom_gap > 0 THEN i.classroom_gap ELSE 0 END
            * (0.7 + (CRC32(CONCAT(i.school_id, i.academic_year, 'cr')) MOD 80) / 100.0)
        )),
        -- Teacher request: actual gap × (0.7 to 1.5)
        GREATEST(0, ROUND(
            CASE WHEN t.teacher_gap > 0 THEN t.teacher_gap ELSE 0 END
            * (0.7 + (CRC32(CONCAT(i.school_id, i.academic_year, 'tr')) MOD 80) / 100.0)
        )),
        'SIMULATION'
    FROM infrastructure_details i
    LEFT JOIN teacher_metrics t
        ON i.school_id = t.school_id AND i.academic_year = t.academic_year
    WHERE i.academic_year = :year
""")

# ── Validate proposals against actual gaps ───────────────────────────────────
# Decision logic:
#   ACCEPTED:  request within ±20% of actual gap (ratio 0.8–1.2)
#   FLAGGED:   request 20–50% over actual gap (ratio 1.2–1.5)
#              or request 50-80% of actual gap (ratio 0.5–0.8, under-requesting)
#   REJECTED:  request >50% over actual gap (ratio >1.5, over-requesting)
#              or request <50% of actual gap with existing gap (under-requesting)
#   Also: if school has NO gap but requests resources → REJECTED (NO_DEFICIT)

VALIDATE_SQL = text("""
    INSERT INTO proposal_validations
        (school_id, academic_year, requested_classrooms, requested_teachers,
         actual_classroom_gap, actual_teacher_gap, classroom_ratio,
         teacher_ratio, decision_status, reason_code, confidence_score)
    SELECT
        p.school_id,
        p.academic_year,
        p.requested_classrooms,
        p.requested_teachers,
        CASE WHEN i.classroom_gap > 0 THEN i.classroom_gap ELSE 0 END AS actual_cr_gap,
        CASE WHEN t.teacher_gap > 0 THEN t.teacher_gap ELSE 0 END     AS actual_tr_gap,
        -- Classroom ratio: requested / actual (NULL if no gap)
        ROUND(
            p.requested_classrooms /
            NULLIF(CASE WHEN i.classroom_gap > 0 THEN i.classroom_gap ELSE 0 END, 0),
            4
        ) AS classroom_ratio,
        -- Teacher ratio
        ROUND(
            p.requested_teachers /
            NULLIF(CASE WHEN t.teacher_gap > 0 THEN t.teacher_gap ELSE 0 END, 0),
            4
        ) AS teacher_ratio,
        -- Decision logic (worst-case across both dimensions)
        CASE
            -- No deficit but requesting resources
            WHEN (IFNULL(i.classroom_gap, 0) <= 0 AND p.requested_classrooms > 0)
              OR (IFNULL(t.teacher_gap, 0) <= 0 AND p.requested_teachers > 0)
            THEN 'REJECTED'
            -- Severe over-requesting (>1.5x on either dimension)
            WHEN p.requested_classrooms > 0 AND i.classroom_gap > 0 AND
                 p.requested_classrooms > i.classroom_gap * 1.5
            THEN 'REJECTED'
            WHEN p.requested_teachers > 0 AND t.teacher_gap > 0 AND
                 p.requested_teachers > t.teacher_gap * 1.5
            THEN 'REJECTED'
            -- Moderate deviation (flagged)
            WHEN p.requested_classrooms > 0 AND i.classroom_gap > 0 AND
                 p.requested_classrooms > i.classroom_gap * 1.2
            THEN 'FLAGGED'
            WHEN p.requested_teachers > 0 AND t.teacher_gap > 0 AND
                 p.requested_teachers > t.teacher_gap * 1.2
            THEN 'FLAGGED'
            WHEN p.requested_classrooms > 0 AND i.classroom_gap > 0 AND
                 p.requested_classrooms < i.classroom_gap * 0.5
            THEN 'FLAGGED'
            WHEN p.requested_teachers > 0 AND t.teacher_gap > 0 AND
                 p.requested_teachers < t.teacher_gap * 0.5
            THEN 'FLAGGED'
            -- No request and no gap = trivially ok
            WHEN p.requested_classrooms = 0 AND p.requested_teachers = 0
            THEN 'ACCEPTED'
            -- Within tolerance
            ELSE 'ACCEPTED'
        END AS decision_status,
        -- Reason code
        CASE
            WHEN (IFNULL(i.classroom_gap, 0) <= 0 AND p.requested_classrooms > 0)
              OR (IFNULL(t.teacher_gap, 0) <= 0 AND p.requested_teachers > 0)
            THEN 'NO_DEFICIT'
            WHEN p.requested_classrooms > 0 AND i.classroom_gap > 0 AND
                 p.requested_classrooms > i.classroom_gap * 1.5
            THEN 'CLASSROOM_OVER_REQUEST'
            WHEN p.requested_teachers > 0 AND t.teacher_gap > 0 AND
                 p.requested_teachers > t.teacher_gap * 1.5
            THEN 'TEACHER_OVER_REQUEST'
            WHEN p.requested_classrooms > 0 AND i.classroom_gap > 0 AND
                 p.requested_classrooms > i.classroom_gap * 1.2
            THEN 'CLASSROOM_MODERATE_OVER'
            WHEN p.requested_teachers > 0 AND t.teacher_gap > 0 AND
                 p.requested_teachers > t.teacher_gap * 1.2
            THEN 'TEACHER_MODERATE_OVER'
            WHEN p.requested_classrooms > 0 AND i.classroom_gap > 0 AND
                 p.requested_classrooms < i.classroom_gap * 0.5
            THEN 'CLASSROOM_UNDER_REQUEST'
            WHEN p.requested_teachers > 0 AND t.teacher_gap > 0 AND
                 p.requested_teachers < t.teacher_gap * 0.5
            THEN 'TEACHER_UNDER_REQUEST'
            WHEN p.requested_classrooms = 0 AND p.requested_teachers = 0
            THEN 'NO_REQUEST'
            ELSE 'WITHIN_TOLERANCE'
        END AS reason_code,
        -- Confidence score: 1.0 = perfect match,
        -- degrades with ratio deviation from 1.0
        ROUND(
            GREATEST(0,
                1.0 - (
                    ABS(1.0 - IFNULL(
                        p.requested_classrooms /
                        NULLIF(CASE WHEN i.classroom_gap > 0 THEN i.classroom_gap ELSE 0 END, 0),
                        1.0
                    ))
                    +
                    ABS(1.0 - IFNULL(
                        p.requested_teachers /
                        NULLIF(CASE WHEN t.teacher_gap > 0 THEN t.teacher_gap ELSE 0 END, 0),
                        1.0
                    ))
                ) / 2.0
            ),
            4
        ) AS confidence_score
    FROM school_demand_proposals p
    JOIN infrastructure_details i
        ON p.school_id = i.school_id AND p.academic_year = i.academic_year
    LEFT JOIN teacher_metrics t
        ON p.school_id = t.school_id AND p.academic_year = t.academic_year
    WHERE p.academic_year = :year
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
        COUNT(*)                                                         AS total,
        SUM(CASE WHEN decision_status = 'ACCEPTED' THEN 1 ELSE 0 END)   AS accepted,
        SUM(CASE WHEN decision_status = 'FLAGGED'  THEN 1 ELSE 0 END)   AS flagged,
        SUM(CASE WHEN decision_status = 'REJECTED' THEN 1 ELSE 0 END)   AS rejected,
        ROUND(AVG(confidence_score), 4)                                  AS avg_confidence,
        SUM(CASE WHEN reason_code = 'NO_DEFICIT'             THEN 1 ELSE 0 END) AS no_deficit,
        SUM(CASE WHEN reason_code = 'CLASSROOM_OVER_REQUEST' THEN 1 ELSE 0 END) AS cr_over,
        SUM(CASE WHEN reason_code = 'TEACHER_OVER_REQUEST'   THEN 1 ELSE 0 END) AS tr_over,
        SUM(CASE WHEN reason_code = 'WITHIN_TOLERANCE'       THEN 1 ELSE 0 END) AS within_tol,
        SUM(CASE WHEN reason_code = 'NO_REQUEST'             THEN 1 ELSE 0 END) AS no_request
    FROM proposal_validations
""")

DISTRICT_VALIDATION_SQL = text("""
    SELECT
        s.district,
        COUNT(*)                                                       AS proposals,
        SUM(CASE WHEN v.decision_status = 'ACCEPTED' THEN 1 ELSE 0 END) AS accepted,
        SUM(CASE WHEN v.decision_status = 'FLAGGED'  THEN 1 ELSE 0 END) AS flagged,
        SUM(CASE WHEN v.decision_status = 'REJECTED' THEN 1 ELSE 0 END) AS rejected,
        ROUND(AVG(v.confidence_score), 4)                               AS avg_conf
    FROM proposal_validations v
    JOIN schools s ON v.school_id = s.school_id
    WHERE v.academic_year = (
        SELECT MAX(academic_year) FROM proposal_validations
    )
    GROUP BY s.district
    ORDER BY rejected DESC
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

    # ── Step 1: Create tables ────────────────────────────────────────────
    print("Step 1/6 — Ensuring tables exist...")
    with engine.begin() as conn:
        conn.execute(CREATE_PROPOSALS_SQL)
        conn.execute(CREATE_VALIDATIONS_SQL)
    print("  [OK] Tables ready.\n")

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
        conn.execute(text("DELETE FROM proposal_validations"))
        conn.execute(text("DELETE FROM school_demand_proposals"))
    print("  [OK] Cleared.\n")

    # ── Step 4: Seed proposals ───────────────────────────────────────────
    with engine.connect() as conn:
        years = [r["academic_year"] for r in conn.execute(YEARS_SQL).mappings().all()]

    print("Step 4/6 — Generating synthetic demand proposals...")
    t0 = time.time()
    total_p = 0
    for yr in years:
        t_yr = time.time()
        with engine.begin() as conn:
            result = conn.execute(SEED_PROPOSALS_SQL, {"year": yr})
            affected = result.rowcount
            total_p += affected
        print(f"  [OK] {yr}: {affected:,} proposals  ({time.time() - t_yr:.1f}s)")
    print(f"\n  Generated: {total_p:,} proposals in {time.time() - t0:.1f}s.\n")

    # ── Step 5: Validate proposals ───────────────────────────────────────
    print("Step 5/6 — Validating proposals against computed gaps...")
    t0 = time.time()
    total_v = 0
    for yr in years:
        t_yr = time.time()
        with engine.begin() as conn:
            result = conn.execute(VALIDATE_SQL, {"year": yr})
            affected = result.rowcount
            total_v += affected
        print(f"  [OK] {yr}: {affected:,} validated  ({time.time() - t_yr:.1f}s)")
    print(f"\n  Validated: {total_v:,} proposals in {time.time() - t0:.1f}s.\n")

    # ── Step 6: Summary ──────────────────────────────────────────────────
    print("Step 6/6 — Generating summary...")
    with engine.connect() as conn:
        stats = conn.execute(STATS_SQL).mappings().first()
        districts = conn.execute(DISTRICT_VALIDATION_SQL).mappings().all()

    sep = "=" * 62
    dash = "-" * 58
    lines = [
        "", sep,
        "Proposal Validation Engine — Summary",
        sep,
        f"Total proposals validated   : {int(stats['total']):,}",
        f"  ACCEPTED      : {int(stats['accepted']):>7,}",
        f"  FLAGGED       : {int(stats['flagged']):>7,}",
        f"  REJECTED      : {int(stats['rejected']):>7,}",
        f"  Avg confidence: {stats['avg_confidence']}",
        "",
        "Reason code breakdown:",
        f"  WITHIN_TOLERANCE       : {int(stats['within_tol']):>7,}",
        f"  NO_REQUEST             : {int(stats['no_request']):>7,}",
        f"  NO_DEFICIT             : {int(stats['no_deficit']):>7,}",
        f"  CLASSROOM_OVER_REQUEST : {int(stats['cr_over']):>7,}",
        f"  TEACHER_OVER_REQUEST   : {int(stats['tr_over']):>7,}",
        "",
        "Top 10 Districts by Rejections (latest year):",
        dash,
    ]
    for d in districts:
        district = str(d["district"] or "").strip()
        lines.append(
            f"  {district:22s}"
            f"  total: {int(d['proposals']):>5,}"
            f"  acc: {int(d['accepted']):>5,}"
            f"  flag: {int(d['flagged']):>4,}"
            f"  rej: {int(d['rejected']):>4,}"
            f"  conf: {d['avg_conf']}"
        )
    lines.append(dash)
    print("\n".join(lines))


if __name__ == "__main__":
    print("=" * 62)
    print("  School AI BAV — Proposal Validation Engine (v1.0)")
    print("=" * 62 + "\n")
    run()
