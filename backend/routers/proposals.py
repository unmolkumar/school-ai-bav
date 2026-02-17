"""
proposals.py — Proposal submission + validation + configurable budget simulation.

Fixes two limitations from the system design:
  1. "No real proposal data" → Real proposal submission endpoint
  2. "Fixed budget parameters" → Configurable budget simulation
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from backend.database import query, execute, engine
from sqlalchemy import text
import math

router = APIRouter()


# ═══════════════════════════════════════════════════════════════
#  TABLE: school_proposals (real submissions)
# ═══════════════════════════════════════════════════════════════

PROPOSALS_DDL = """
CREATE TABLE IF NOT EXISTS school_proposals (
    id                    INT AUTO_INCREMENT PRIMARY KEY,
    school_id             VARCHAR(50)   NOT NULL,
    academic_year         VARCHAR(20)   NOT NULL,
    classrooms_requested  INT           DEFAULT 0,
    teachers_requested    INT           DEFAULT 0,
    justification         TEXT,
    submitted_by          VARCHAR(100),
    submitted_at          DATETIME      DEFAULT CURRENT_TIMESTAMP,
    decision_status       VARCHAR(20)   DEFAULT 'PENDING',
    reason_code           VARCHAR(50),
    classroom_ratio       FLOAT,
    teacher_ratio         FLOAT,
    confidence_score      FLOAT,
    validated_at          DATETIME,
    INDEX idx_sp_school (school_id, academic_year)
)
"""

# Ensure table exists on module load
try:
    execute(PROPOSALS_DDL)
except Exception:
    pass


# ═══════════════════════════════════════════════════════════════
#  PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════

class ProposalInput(BaseModel):
    school_id: str
    academic_year: str
    classrooms_requested: int = Field(ge=0, le=100)
    teachers_requested: int = Field(ge=0, le=100)
    justification: Optional[str] = ""
    submitted_by: Optional[str] = "School Admin"


class BudgetParams(BaseModel):
    year: Optional[str] = None
    total_budget_cr: float = Field(default=50.0, ge=1, le=500, description="Total budget in crores")
    cost_per_classroom_lakh: float = Field(default=5.0, ge=1, le=50, description="Cost per classroom in lakhs")
    max_teachers: int = Field(default=10000, ge=100, le=100000, description="Maximum teacher postings")


# ═══════════════════════════════════════════════════════════════
#  PROPOSAL SUBMISSION & VALIDATION
# ═══════════════════════════════════════════════════════════════

NORMS = {1: (30, 30), 2: (30, 30), 3: (30, 30), 4: (35, 30), 5: (35, 30),
         6: (40, 35), 7: (40, 35), 8: (40, 35), 9: (40, 35), 10: (40, 35), 11: (40, 35)}


def validate_proposal(school_id: str, year: str, cr_req: int, tr_req: int):
    """Validate a proposal against actual gaps — real-time decision."""
    gaps = query("""
        SELECT i.classroom_gap, IFNULL(t.teacher_gap, 0) AS teacher_gap,
               i.required_class_rooms, IFNULL(t.required_teachers, 0) AS required_teachers
        FROM infrastructure_details i
        LEFT JOIN teacher_metrics t ON i.school_id = t.school_id AND i.academic_year = t.academic_year
        WHERE i.school_id = :sid AND i.academic_year = :y
    """, {"sid": school_id, "y": year})

    if not gaps:
        return "REJECTED", "SCHOOL_NOT_FOUND", None, None, 0.0

    g = gaps[0]
    cr_gap = g["classroom_gap"] or 0
    tr_gap = g["teacher_gap"] or 0

    cr_ratio = cr_req / max(cr_gap, 1) if cr_gap > 0 else (float("inf") if cr_req > 0 else 0)
    tr_ratio = tr_req / max(tr_gap, 1) if tr_gap > 0 else (float("inf") if tr_req > 0 else 0)

    # Decision tree (same as Phase 9)
    if cr_gap == 0 and tr_gap == 0 and (cr_req > 0 or tr_req > 0):
        return "REJECTED", "NO_DEFICIT", cr_ratio, tr_ratio, 0.1

    if cr_ratio > 1.5:
        return "REJECTED", "CLASSROOM_OVER_REQUEST", cr_ratio, tr_ratio, 0.2

    if tr_ratio > 1.5:
        return "REJECTED", "TEACHER_OVER_REQUEST", cr_ratio, tr_ratio, 0.2

    if 1.2 <= cr_ratio <= 1.5:
        return "FLAGGED", "CLASSROOM_MODERATE_OVER", cr_ratio, tr_ratio, 0.5

    if 1.2 <= tr_ratio <= 1.5:
        return "FLAGGED", "TEACHER_MODERATE_OVER", cr_ratio, tr_ratio, 0.5

    if cr_ratio < 0.5 and cr_gap > 0:
        return "FLAGGED", "CLASSROOM_UNDER_REQUEST", cr_ratio, tr_ratio, 0.6

    if tr_ratio < 0.5 and tr_gap > 0:
        return "FLAGGED", "TEACHER_UNDER_REQUEST", cr_ratio, tr_ratio, 0.6

    if cr_req == 0 and tr_req == 0 and cr_gap == 0 and tr_gap == 0:
        return "ACCEPTED", "NO_REQUEST", 0, 0, 1.0

    # Within tolerance
    confidence = max(0.0, min(1.0, 1.0 - abs(cr_ratio - 1.0) * 0.5 - abs(tr_ratio - 1.0) * 0.5))
    return "ACCEPTED", "WITHIN_TOLERANCE", cr_ratio, tr_ratio, round(confidence, 3)


@router.post("/submit")
def submit_proposal(p: ProposalInput):
    """Submit a real school proposal and get instant validation."""
    # Validate
    status, reason, cr_r, tr_r, conf = validate_proposal(
        p.school_id, p.academic_year, p.classrooms_requested, p.teachers_requested
    )

    # Insert
    execute("""
        INSERT INTO school_proposals
            (school_id, academic_year, classrooms_requested, teachers_requested,
             justification, submitted_by, decision_status, reason_code,
             classroom_ratio, teacher_ratio, confidence_score, validated_at)
        VALUES
            (:sid, :y, :cr, :tr, :just, :by, :status, :reason,
             :crr, :trr, :conf, NOW())
    """, {
        "sid": p.school_id, "y": p.academic_year,
        "cr": p.classrooms_requested, "tr": p.teachers_requested,
        "just": p.justification, "by": p.submitted_by,
        "status": status, "reason": reason,
        "crr": cr_r, "trr": tr_r, "conf": conf,
    })

    # Get gap context for response
    gaps = query("""
        SELECT i.classroom_gap, IFNULL(t.teacher_gap, 0) AS teacher_gap,
               y.total_enrolment
        FROM infrastructure_details i
        LEFT JOIN teacher_metrics t ON i.school_id = t.school_id AND i.academic_year = t.academic_year
        LEFT JOIN yearly_metrics y ON i.school_id = y.school_id AND i.academic_year = y.academic_year
        WHERE i.school_id = :sid AND i.academic_year = :y
    """, {"sid": p.school_id, "y": p.academic_year})

    return {
        "decision_status": status,
        "reason_code": reason,
        "confidence_score": conf,
        "classroom_ratio": cr_r,
        "teacher_ratio": tr_r,
        "actual_gaps": gaps[0] if gaps else {},
        "message": {
            "ACCEPTED": "Proposal accepted — within tolerance of actual gaps.",
            "FLAGGED": f"Proposal flagged for manual review — {reason.replace('_', ' ').lower()}.",
            "REJECTED": f"Proposal rejected — {reason.replace('_', ' ').lower()}.",
        }.get(status, ""),
    }


@router.get("/school/{school_id}")
def get_school_proposals(school_id: str):
    """Get all proposals for a school."""
    rows = query("""
        SELECT id, school_id, academic_year, classrooms_requested, teachers_requested,
               justification, submitted_by, submitted_at,
               decision_status, reason_code, confidence_score,
               classroom_ratio, teacher_ratio, validated_at
        FROM school_proposals
        WHERE school_id = :sid
        ORDER BY submitted_at DESC
    """, {"sid": school_id})
    return rows


# ═══════════════════════════════════════════════════════════════
#  CONFIGURABLE BUDGET SIMULATION
# ═══════════════════════════════════════════════════════════════

@router.post("/budget/simulate")
def simulate_budget(params: BudgetParams):
    """Run budget simulation with custom parameters (non-destructive)."""
    if not params.year:
        r = query("SELECT MAX(academic_year) AS y FROM infrastructure_details")
        params.year = r[0]["y"]

    cost_per_cr = params.cost_per_classroom_lakh * 100000  # ₹ lakhs → ₹
    max_classrooms = int(params.total_budget_cr * 10000000 / cost_per_cr)

    # Get schools ranked by priority
    schools = query("""
        SELECT sp.school_id, sp.state_rank AS risk_rank, sp.risk_score,
               IFNULL(i.classroom_gap, 0) AS classroom_gap,
               IFNULL(t.teacher_gap, 0) AS teacher_gap,
               s.district, s.block
        FROM school_priority_index sp
        JOIN infrastructure_details i ON sp.school_id = i.school_id AND sp.academic_year = i.academic_year
        LEFT JOIN teacher_metrics t ON sp.school_id = t.school_id AND sp.academic_year = t.academic_year
        JOIN schools s ON sp.school_id = s.school_id
        WHERE sp.academic_year = :y
        ORDER BY sp.state_rank ASC
    """, {"y": params.year})

    # Simulate allocation
    cum_cr = 0
    cum_tr = 0
    cum_cost = 0
    funded = 0
    partial = 0
    unfunded = 0
    district_alloc = {}

    for s in schools:
        cr_alloc = 0
        tr_alloc = 0
        cr_gap = s["classroom_gap"] or 0
        tr_gap = s["teacher_gap"] or 0

        if cum_cr + cr_gap <= max_classrooms:
            cr_alloc = cr_gap
        elif cum_cr < max_classrooms:
            cr_alloc = max_classrooms - cum_cr

        if cum_tr + tr_gap <= params.max_teachers:
            tr_alloc = tr_gap
        elif cum_tr < params.max_teachers:
            tr_alloc = params.max_teachers - cum_tr

        cum_cr += cr_alloc
        cum_tr += tr_alloc
        cost = cr_alloc * cost_per_cr
        cum_cost += cost

        if cr_alloc > 0 or tr_alloc > 0:
            if cr_alloc >= cr_gap and tr_alloc >= tr_gap:
                funded += 1
            else:
                partial += 1
        else:
            unfunded += 1

        d = s["district"]
        if d not in district_alloc:
            district_alloc[d] = {"district": d, "classrooms": 0, "teachers": 0, "cost": 0, "schools_served": 0}
        district_alloc[d]["classrooms"] += cr_alloc
        district_alloc[d]["teachers"] += tr_alloc
        district_alloc[d]["cost"] += cost
        if cr_alloc > 0 or tr_alloc > 0:
            district_alloc[d]["schools_served"] += 1

    return {
        "params": {
            "year": params.year,
            "total_budget_cr": params.total_budget_cr,
            "cost_per_classroom_lakh": params.cost_per_classroom_lakh,
            "max_teachers": params.max_teachers,
            "max_classrooms": max_classrooms,
        },
        "summary": {
            "funded": funded,
            "partially_funded": partial,
            "unfunded": unfunded,
            "total_schools": len(schools),
            "classrooms_allocated": cum_cr,
            "teachers_allocated": cum_tr,
            "total_cost_cr": round(cum_cost / 10000000, 2),
            "budget_utilisation_pct": round(cum_cost / (params.total_budget_cr * 10000000) * 100, 1),
        },
        "by_district": sorted(district_alloc.values(), key=lambda x: -x["classrooms"])[:15],
    }
