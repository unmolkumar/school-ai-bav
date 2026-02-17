"""
district.py — District-level dashboard API endpoints.

Panels:
  1. Compliance Card (grade + gauge + trend)
  2. Block-wise Heatmap (blocks × risk levels)
  3. Priority Schools (TOP_5/TOP_10)
  4. Proposal Validation Summary
  5. District Trend Line (7-year)
"""
from fastapi import APIRouter, Query
from backend.database import query

router = APIRouter()


@router.get("/list")
def list_districts():
    """List all districts with latest compliance data."""
    rows = query("""
        SELECT d.district, d.compliance_grade, d.avg_risk_score, d.district_rank,
               d.yoy_risk_improvement, d.total_schools,
               d.pct_high_critical,
               d.academic_year
        FROM district_compliance_index d
        WHERE d.academic_year = (SELECT MAX(academic_year) FROM district_compliance_index)
        ORDER BY d.district_rank
    """)
    return rows


@router.get("/{district_name}/compliance")
def district_compliance(district_name: str):
    """Compliance card — grade, gauge, trend arrow, rank."""
    rows = query("""
        SELECT district, academic_year, compliance_grade, avg_risk_score,
               district_rank, yoy_risk_improvement, total_schools,
               pct_high_critical
        FROM district_compliance_index
        WHERE district = :d
        ORDER BY academic_year
    """, {"d": district_name})
    return rows


@router.get("/{district_name}/blocks")
def district_blocks(district_name: str, year: str = None):
    """Block-wise risk heatmap data."""
    if not year:
        r = query("SELECT MAX(academic_year) AS y FROM infrastructure_details")
        year = r[0]["y"]

    rows = query("""
        SELECT
            IFNULL(s.block, 'UNKNOWN') AS block,
            i.risk_level,
            COUNT(*) AS count
        FROM infrastructure_details i
        JOIN schools s ON i.school_id = s.school_id
        WHERE s.district = :d AND i.academic_year = :y
        GROUP BY s.block, i.risk_level
        ORDER BY s.block, i.risk_level
    """, {"d": district_name, "y": year})

    # Pivot into {block: {CRITICAL: n, HIGH: n, ...}}
    blocks = {}
    for r in rows:
        b = r["block"]
        if b not in blocks:
            blocks[b] = {"block": b, "CRITICAL": 0, "HIGH": 0, "MODERATE": 0, "LOW": 0, "total": 0}
        blocks[b][r["risk_level"]] = r["count"]
        blocks[b]["total"] += r["count"]

    return {"year": year, "blocks": list(blocks.values())}


@router.get("/{district_name}/priority")
def district_priority(district_name: str, year: str = None):
    """Priority schools — TOP_5% and TOP_10% with risk details."""
    if not year:
        r = query("SELECT MAX(academic_year) AS y FROM school_priority_index")
        year = r[0]["y"]

    rows = query("""
        SELECT p.school_id, s.school_name, s.block,
               p.risk_score, p.state_rank,
               p.priority_bucket, p.persistent_high_risk_flag,
               i.classroom_gap, i.risk_level,
               IFNULL(t.teacher_gap, 0) AS teacher_gap
        FROM school_priority_index p
        JOIN schools s ON p.school_id = s.school_id
        JOIN infrastructure_details i ON p.school_id = i.school_id AND p.academic_year = i.academic_year
        LEFT JOIN teacher_metrics t ON p.school_id = t.school_id AND p.academic_year = t.academic_year
        WHERE s.district = :d AND p.academic_year = :y
          AND p.priority_bucket IN ('TOP_5', 'TOP_10')
        ORDER BY p.state_rank
        LIMIT 50
    """, {"d": district_name, "y": year})

    return {"year": year, "schools": rows}


@router.get("/{district_name}/proposals")
def district_proposals(district_name: str, year: str = None):
    """Proposal validation summary — pie chart + flagged list."""
    if not year:
        r = query("SELECT MAX(academic_year) AS y FROM proposal_validations")
        year = r[0]["y"]

    summary = query("""
        SELECT pv.decision_status, COUNT(*) AS count
        FROM proposal_validations pv
        JOIN schools s ON pv.school_id = s.school_id
        WHERE s.district = :d AND pv.academic_year = :y
        GROUP BY pv.decision_status
    """, {"d": district_name, "y": year})

    flagged = query("""
        SELECT pv.school_id, s.school_name, s.block,
               pv.decision_status, pv.reason_code, pv.confidence_score,
               pv.classroom_ratio, pv.teacher_ratio
        FROM proposal_validations pv
        JOIN schools s ON pv.school_id = s.school_id
        WHERE s.district = :d AND pv.academic_year = :y
          AND pv.decision_status = 'FLAGGED'
        ORDER BY pv.confidence_score ASC
        LIMIT 30
    """, {"d": district_name, "y": year})

    return {"year": year, "summary": summary, "flagged": flagged}


@router.get("/{district_name}/trend")
def district_trend(district_name: str):
    """7-year district trend line."""
    rows = query("""
        SELECT academic_year, avg_risk_score, compliance_grade,
               district_rank, yoy_risk_improvement, total_schools,
               pct_high_critical
        FROM district_compliance_index
        WHERE district = :d
        ORDER BY academic_year
    """, {"d": district_name})
    return rows
