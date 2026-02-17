"""
state.py — State-level dashboard API endpoints.

Panels:
  1. Risk Overview (choropleth data + KPIs)
  2. Trend Sparklines (7-year state trends)
  3. Budget Simulation Summary
  4. Forecasting Alert (T+1/T+2/T+3)
"""
from fastapi import APIRouter, Query
from backend.database import query

router = APIRouter()


@router.get("/overview")
def state_overview(year: str = None):
    """KPIs + district compliance data for the state overview map."""
    if not year:
        r = query("SELECT MAX(academic_year) AS y FROM infrastructure_details")
        year = r[0]["y"]

    kpis = query("""
        SELECT
            COUNT(DISTINCT i.school_id) AS total_schools,
            SUM(CASE WHEN i.risk_level = 'CRITICAL' THEN 1 ELSE 0 END) AS critical_schools,
            SUM(CASE WHEN i.risk_level = 'HIGH' THEN 1 ELSE 0 END)     AS high_schools,
            SUM(CASE WHEN i.risk_level = 'MODERATE' THEN 1 ELSE 0 END) AS moderate_schools,
            SUM(CASE WHEN i.risk_level = 'LOW' THEN 1 ELSE 0 END)      AS low_schools,
            ROUND(AVG(i.risk_score), 4) AS avg_risk_score,
            SUM(i.classroom_gap) AS total_classroom_gap,
            SUM(IFNULL(t.teacher_gap, 0)) AS total_teacher_gap
        FROM infrastructure_details i
        LEFT JOIN teacher_metrics t ON i.school_id = t.school_id AND i.academic_year = t.academic_year
        WHERE i.academic_year = :year
    """, {"year": year})

    budget = query("""
        SELECT
            SUM(CASE WHEN classroom_resolved = 1 AND teacher_resolved = 1 THEN 1 ELSE 0 END) AS funded,
            SUM(CASE WHEN (classroom_resolved = 1 OR teacher_resolved = 1)
                      AND NOT (classroom_resolved = 1 AND teacher_resolved = 1) THEN 1 ELSE 0 END) AS partial,
            SUM(CASE WHEN classroom_resolved = 0 AND teacher_resolved = 0 THEN 1 ELSE 0 END) AS unfunded,
            SUM(classrooms_allocated) AS total_classrooms_allocated,
            SUM(teachers_allocated) AS total_teachers_allocated
        FROM budget_simulation
        WHERE academic_year = :year
    """, {"year": year})

    districts = query("""
        SELECT district, academic_year, total_schools, avg_risk_score,
               compliance_grade, district_rank, yoy_risk_improvement,
               pct_high_critical
        FROM district_compliance_index
        WHERE academic_year = :year
        ORDER BY district_rank
    """, {"year": year})

    return {
        "year": year,
        "kpis": kpis[0] if kpis else {},
        "budget": budget[0] if budget else {},
        "districts": districts,
    }


@router.get("/years")
def available_years():
    """List all academic years in the dataset."""
    rows = query("SELECT DISTINCT academic_year FROM yearly_metrics ORDER BY academic_year")
    return [r["academic_year"] for r in rows]


@router.get("/trends")
def state_trends():
    """7-year state-wide risk trends for sparkline charts."""
    risk_by_year = query("""
        SELECT academic_year,
               ROUND(AVG(risk_score), 4) AS avg_risk,
               SUM(CASE WHEN risk_level='CRITICAL' THEN 1 ELSE 0 END) AS critical,
               SUM(CASE WHEN risk_level='HIGH' THEN 1 ELSE 0 END) AS high,
               SUM(CASE WHEN risk_level='MODERATE' THEN 1 ELSE 0 END) AS moderate,
               SUM(CASE WHEN risk_level='LOW' THEN 1 ELSE 0 END) AS low,
               COUNT(*) AS total
        FROM infrastructure_details
        GROUP BY academic_year
        ORDER BY academic_year
    """)

    enrolment_by_year = query("""
        SELECT academic_year,
               SUM(total_enrolment) AS total_enrolment,
               COUNT(DISTINCT school_id) AS school_count
        FROM yearly_metrics
        GROUP BY academic_year
        ORDER BY academic_year
    """)

    return {"risk_trends": risk_by_year, "enrolment_trends": enrolment_by_year}


@router.get("/budget")
def budget_summary(year: str = None):
    """Budget allocation summary — funded/unfunded/partial breakdown."""
    if not year:
        r = query("SELECT MAX(academic_year) AS y FROM budget_simulation")
        year = r[0]["y"]

    by_status = query("""
        SELECT
            CASE
              WHEN classroom_resolved = 1 AND teacher_resolved = 1 THEN 'FUNDED'
              WHEN classroom_resolved = 1 OR teacher_resolved = 1 THEN 'PARTIALLY_FUNDED'
              ELSE 'UNFUNDED'
            END AS allocation_status,
            COUNT(*) AS count,
            SUM(classrooms_allocated) AS classrooms,
            SUM(teachers_allocated) AS teachers
        FROM budget_simulation
        WHERE academic_year = :year
        GROUP BY allocation_status
    """, {"year": year})

    top_unfunded = query("""
        SELECT s.district,
               SUM(b.classroom_gap - b.classrooms_allocated) AS unfunded_cr_gap,
               SUM(b.teacher_gap - b.teachers_allocated) AS unfunded_tr_gap,
               COUNT(*) AS schools
        FROM budget_simulation b
        JOIN schools s ON b.school_id = s.school_id
        WHERE b.academic_year = :year
          AND b.classroom_resolved = 0 AND b.teacher_resolved = 0
        GROUP BY s.district
        ORDER BY unfunded_cr_gap DESC
        LIMIT 10
    """, {"year": year})

    return {"year": year, "by_status": by_status, "top_unfunded_districts": top_unfunded}


@router.get("/forecast")
def forecast_summary():
    """Forecast gaps at T+1, T+2, T+3 — Phase 10 (WMA) and Phase 11 (ML)."""
    wma = query("""
        SELECT years_ahead, forecast_year,
               SUM(projected_classroom_gap) AS cr_gap,
               SUM(projected_teacher_gap) AS tr_gap,
               ROUND(AVG(avg_growth_rate), 4) AS mean_growth,
               SUM(projected_enrolment) AS total_enrolment
        FROM enrolment_forecast
        GROUP BY years_ahead, forecast_year
        ORDER BY years_ahead
    """)

    ml = query("""
        SELECT years_ahead, forecast_year,
               SUM(projected_classroom_gap) AS cr_gap,
               SUM(projected_teacher_gap) AS tr_gap,
               ROUND(AVG(ml_growth_rate), 4) AS mean_growth,
               SUM(projected_enrolment) AS total_enrolment
        FROM ml_enrolment_forecast
        GROUP BY years_ahead, forecast_year
        ORDER BY years_ahead
    """)

    top_districts = query("""
        SELECT s.district,
               SUM(m.projected_classroom_gap) AS cr_gap,
               SUM(m.projected_teacher_gap) AS tr_gap,
               SUM(m.projected_enrolment) AS enrolment,
               ROUND(AVG(m.ml_growth_rate), 4) AS growth
        FROM ml_enrolment_forecast m
        JOIN schools s ON m.school_id = s.school_id
        WHERE m.years_ahead = 3
        GROUP BY s.district
        ORDER BY cr_gap DESC
        LIMIT 10
    """)

    return {"wma": wma, "ml": ml, "top_districts_t3": top_districts}
