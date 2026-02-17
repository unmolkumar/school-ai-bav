"""
school.py — School-level & Block-level dashboard API endpoints.

Block Panels:
  1. Block Summary (KPIs)
  2. School List (all schools with indicators)
  3. Chronic & Volatile schools

School Panels:
  1. Risk Card (score + level + trend)
  2. Gap Analysis (classrooms + teachers)
  3. Proposal Status
  4. Forecast (T+1/T+2/T+3)
  5. Facility Checklist
"""
from fastapi import APIRouter, Query
from backend.database import query

router = APIRouter()


# ═══════════════════════════════════════════════════════════════
#  BLOCK-LEVEL ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/block/{district}/{block}/summary")
def block_summary(district: str, block: str, year: str = None):
    """Block-level KPIs."""
    if not year:
        r = query("SELECT MAX(academic_year) AS y FROM infrastructure_details")
        year = r[0]["y"]

    kpis = query("""
        SELECT
            COUNT(DISTINCT i.school_id) AS total_schools,
            SUM(CASE WHEN i.risk_level = 'CRITICAL' THEN 1 ELSE 0 END) AS critical,
            SUM(CASE WHEN i.risk_level = 'HIGH' THEN 1 ELSE 0 END) AS high,
            SUM(CASE WHEN i.risk_level = 'MODERATE' THEN 1 ELSE 0 END) AS moderate,
            SUM(CASE WHEN i.risk_level = 'LOW' THEN 1 ELSE 0 END) AS low,
            ROUND(AVG(i.risk_score), 4) AS avg_risk_score,
            SUM(i.classroom_gap) AS total_classroom_gap,
            SUM(IFNULL(t.teacher_gap, 0)) AS total_teacher_gap
        FROM infrastructure_details i
        JOIN schools s ON i.school_id = s.school_id
        LEFT JOIN teacher_metrics t ON i.school_id = t.school_id AND i.academic_year = t.academic_year
        WHERE s.district = :d AND IFNULL(s.block, 'UNKNOWN') = :b AND i.academic_year = :y
    """, {"d": district, "b": block, "y": year})

    funded = query("""
        SELECT COUNT(*) AS funded_count
        FROM budget_simulation bs
        JOIN schools s ON bs.school_id = s.school_id
        WHERE s.district = :d AND IFNULL(s.block, 'UNKNOWN') = :b
          AND bs.academic_year = :y AND bs.classroom_resolved = 1 AND bs.teacher_resolved = 1
    """, {"d": district, "b": block, "y": year})

    return {
        "year": year,
        "district": district,
        "block": block,
        "kpis": kpis[0] if kpis else {},
        "funded_count": funded[0]["funded_count"] if funded else 0,
    }


@router.get("/block/{district}/{block}/schools")
def block_schools(district: str, block: str, year: str = None, limit: int = 100):
    """All schools in a block with risk indicators."""
    if not year:
        r = query("SELECT MAX(academic_year) AS y FROM infrastructure_details")
        year = r[0]["y"]

    rows = query("""
        SELECT i.school_id, s.school_name, s.school_category,
               i.risk_score, i.risk_level, i.classroom_gap,
               IFNULL(t.teacher_gap, 0) AS teacher_gap,
               IFNULL(rt.trend_direction, 'N/A') AS trend_direction,
               IFNULL(rt.chronic_risk_flag, 0) AS is_chronic,
               IFNULL(rt.volatile_flag, 0) AS is_volatile,
               CASE
                 WHEN bs.classroom_resolved = 1 AND bs.teacher_resolved = 1 THEN 'FUNDED'
                 WHEN bs.classroom_resolved = 1 OR bs.teacher_resolved = 1 THEN 'PARTIAL'
                 ELSE 'UNFUNDED'
               END AS budget_status,
               y.total_enrolment
        FROM infrastructure_details i
        JOIN schools s ON i.school_id = s.school_id
        JOIN yearly_metrics y ON i.school_id = y.school_id AND i.academic_year = y.academic_year
        LEFT JOIN teacher_metrics t ON i.school_id = t.school_id AND i.academic_year = t.academic_year
        LEFT JOIN risk_trend rt ON i.school_id = rt.school_id AND i.academic_year = rt.academic_year
        LEFT JOIN budget_simulation bs ON i.school_id = bs.school_id AND i.academic_year = bs.academic_year
        WHERE s.district = :d AND IFNULL(s.block, 'UNKNOWN') = :b AND i.academic_year = :y
        ORDER BY i.risk_score DESC
        LIMIT :lim
    """, {"d": district, "b": block, "y": year, "lim": limit})

    return {"year": year, "schools": rows}


@router.get("/block/{district}/{block}/chronic")
def block_chronic(district: str, block: str, year: str = None):
    """Chronic (3+ years high risk) and volatile schools in a block."""
    if not year:
        r = query("SELECT MAX(academic_year) AS y FROM risk_trend")
        year = r[0]["y"]

    chronic = query("""
        SELECT rt.school_id, s.school_name, rt.risk_score, rt.chronic_risk_flag AS is_chronic, rt.volatile_flag AS is_volatile,
               rt.trend_direction, i.classroom_gap, IFNULL(t.teacher_gap, 0) AS teacher_gap
        FROM risk_trend rt
        JOIN schools s ON rt.school_id = s.school_id
        JOIN infrastructure_details i ON rt.school_id = i.school_id AND rt.academic_year = i.academic_year
        LEFT JOIN teacher_metrics t ON rt.school_id = t.school_id AND rt.academic_year = t.academic_year
        WHERE s.district = :d AND IFNULL(s.block, 'UNKNOWN') = :b
          AND rt.academic_year = :y AND rt.chronic_risk_flag = 1
        ORDER BY rt.risk_score DESC
    """, {"d": district, "b": block, "y": year})

    volatile = query("""
        SELECT rt.school_id, s.school_name, rt.risk_score, rt.risk_delta,
               rt.trend_direction
        FROM risk_trend rt
        JOIN schools s ON rt.school_id = s.school_id
        WHERE s.district = :d AND IFNULL(s.block, 'UNKNOWN') = :b
          AND rt.academic_year = :y AND rt.volatile_flag = 1
        ORDER BY ABS(rt.risk_delta) DESC
        LIMIT 30
    """, {"d": district, "b": block, "y": year})

    return {"year": year, "chronic": chronic, "volatile": volatile}


# ═══════════════════════════════════════════════════════════════
#  SCHOOL-LEVEL ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/{school_id}/overview")
def school_overview(school_id: str):
    """Complete school overview — risk card + gaps + meta."""
    info = query("""
        SELECT s.school_id, s.school_name, s.district, s.block,
               s.school_category, s.management_type
        FROM schools s
        WHERE s.school_id = :sid
    """, {"sid": school_id})

    latest = query("""
        SELECT i.academic_year, i.risk_score, i.risk_level,
               i.classroom_gap, i.required_class_rooms, i.usable_class_rooms,
               i.teacher_deficit_ratio, i.classroom_deficit_ratio,
               IFNULL(t.teacher_gap, 0) AS teacher_gap,
               IFNULL(t.required_teachers, 0) AS required_teachers,
               IFNULL(t.total_teachers, 0) AS total_teachers,
               y.total_enrolment,
               IFNULL(rt.trend_direction, 'N/A') AS trend_direction,
               IFNULL(rt.risk_delta, 0) AS risk_delta,
               IFNULL(rt.chronic_risk_flag, 0) AS is_chronic,
               IFNULL(sp.priority_bucket, 'STANDARD') AS priority_bucket,
               IFNULL(sp.persistent_high_risk_flag, 0) AS persistent_high_risk,
               IFNULL(sp.state_rank, 0) AS risk_rank
        FROM infrastructure_details i
        JOIN yearly_metrics y ON i.school_id = y.school_id AND i.academic_year = y.academic_year
        LEFT JOIN teacher_metrics t ON i.school_id = t.school_id AND i.academic_year = t.academic_year
        LEFT JOIN risk_trend rt ON i.school_id = rt.school_id AND i.academic_year = rt.academic_year
        LEFT JOIN school_priority_index sp ON i.school_id = sp.school_id AND i.academic_year = sp.academic_year
        WHERE i.school_id = :sid
        ORDER BY i.academic_year DESC
        LIMIT 1
    """, {"sid": school_id})

    return {
        "school": info[0] if info else {},
        "latest": latest[0] if latest else {},
    }


@router.get("/{school_id}/history")
def school_history(school_id: str):
    """7-year enrolment and risk history for trend charts."""
    rows = query("""
        SELECT y.academic_year, y.total_enrolment,
               i.risk_score, i.risk_level, i.classroom_gap,
               IFNULL(t.teacher_gap, 0) AS teacher_gap,
               IFNULL(t.total_teachers, 0) AS total_teachers,
               i.usable_class_rooms
        FROM yearly_metrics y
        JOIN infrastructure_details i ON y.school_id = i.school_id AND y.academic_year = i.academic_year
        LEFT JOIN teacher_metrics t ON y.school_id = t.school_id AND y.academic_year = t.academic_year
        WHERE y.school_id = :sid
        ORDER BY y.academic_year
    """, {"sid": school_id})
    return rows


@router.get("/{school_id}/forecast")
def school_forecast(school_id: str):
    """Forecast data for a single school — WMA + ML."""
    wma = query("""
        SELECT forecast_year, years_ahead, base_enrolment,
               avg_growth_rate, projected_enrolment,
               projected_classroom_gap, projected_teacher_gap
        FROM enrolment_forecast
        WHERE school_id = :sid
        ORDER BY years_ahead
    """, {"sid": school_id})

    ml = query("""
        SELECT forecast_year, years_ahead, base_enrolment,
               ml_growth_rate, projected_enrolment,
               projected_classroom_gap, projected_teacher_gap
        FROM ml_enrolment_forecast
        WHERE school_id = :sid
        ORDER BY years_ahead
    """, {"sid": school_id})

    return {"wma": wma, "ml": ml}


@router.get("/{school_id}/facilities")
def school_facilities(school_id: str):
    """Facility checklist — boolean amenities + building condition."""
    rows = query("""
        SELECT i.academic_year,
               i.drinking_water_available AS drinking_water, i.electricity_available AS electricity,
               i.internet_available AS internet,
               i.separate_girls_toilet AS girls_toilet, i.ramp_available AS ramp,
               i.cwsn_toilet_available AS cwsn_toilet, i.resource_room_available AS resource_room,
               i.building_condition, i.classroom_condition_score,
               i.total_class_rooms, i.usable_class_rooms
        FROM infrastructure_details i
        WHERE i.school_id = :sid
        ORDER BY i.academic_year DESC
        LIMIT 1
    """, {"sid": school_id})
    return rows[0] if rows else {}


@router.get("/search")
def search_schools(q: str, limit: int = 20):
    """Search schools by name or ID."""
    rows = query("""
        SELECT school_id, school_name, district, block, school_category
        FROM schools
        WHERE school_id LIKE :q OR school_name LIKE :q
        LIMIT :lim
    """, {"q": f"%{q}%", "lim": limit})
    return rows
