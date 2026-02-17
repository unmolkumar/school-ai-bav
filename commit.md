Phase 1 – Cloud Database Bootstrap (Railway)

- Configured Railway MySQL (public endpoint)
- Secured credentials using .env
- Set up virtual environment
- Installed required DB drivers
- Implemented schema bootstrap script
- Created core tables (schools, yearly_metrics, infrastructure_details, teacher_metrics)
- Verified successful cloud connection

---

Phase 1.1 – Expanded Infrastructure Schema for BAV System

- Redesigned infrastructure_details table to align with Problem Statement 5
- Added norm-based classroom requirement support (total, usable, required, condition score)
- Added CWSN accessibility indicators (ramp, CWSN toilet, resource room)
- Added digital readiness tracking (electricity, internet)
- Added sanitation & gender compliance fields (separate girls toilet)
- Added maintenance lifecycle fields (building condition, last major repair year)
- Improved alignment with AI-driven validation under Problem Statement 5
- Updated ai.md documentation with Phase 1.1 section

---

Phase 1.2 – Implemented Flexible Schema-Mapped Data Loader

- Replaced strict column checks with declarative COLUMN_MAPPING dictionaries
- Mapped CSV columns to four DB tables (schools, yearly_metrics, infrastructure_details, teacher_metrics)
- Computed classroom_condition_score from major/minor repair columns
- Derived cwsn_toilet_available from functional CWSN-friendly flags
- Converted numeric flags (1/2) to native booleans
- Missing CSV columns handled gracefully (default to NULL)
- Idempotent batch inserts inside a single transaction
- Updated ai.md with Phase 1.2 – Flexible Schema Mapping documentation

---

Phase 2 – Implemented Samagra Shiksha Norm-Based Classroom Gap Engine

- Applied Andhra Pradesh Samagra Shiksha classroom norms (30/35/40 students per classroom)
- Mapped all 10 UDISE+ school_category codes to appropriate norms
- Computed required_class_rooms per school-year using ceil(enrolment / norm)
- Calculated classroom_gap = max(required - usable, 0)
- Added classroom_gap column to infrastructure_details (bootstrap + ALTER TABLE)
- Enabled norm-based infrastructure adequacy scoring
- Generated top-10 district deficit ranking
- Idempotent transaction-wrapped batch updates
- Updated ai.md with policy alignment documentation

---

Phase 2 Optimization – Indexing for Scalable Joins

- Added composite index on infrastructure_details (school_id, academic_year)
- Added composite index on yearly_metrics (school_id, academic_year)
- Added index on schools (school_id)
- Safe/idempotent index creation (no failure if index exists)
- Added performance timing to bulk UPDATE execution
- No business logic changes — Samagra Shiksha norms unchanged
- Updated ai.md with indexing optimization documentation

---

Phase 3 – Teacher Adequacy Engine (Samagra Shiksha PTR Norms)

- Implemented AP Samagra Shiksha Pupil-Teacher Ratio norms:
  - Primary (Cat 1): PTR 30:1 — RTE Act 2009, Section 25 / Schedule
  - Upper Primary (Cat 4): PTR 35:1 — RTE Act 2009, Section 25 / Schedule
  - Secondary (Cat 8): PTR 30:1 — RMSA Framework / Samagra Shiksha 2018
  - Senior Secondary (Cat 11): PTR 30:1 — Samagra Shiksha Framework 2018
  - Blended categories (Cat 2,3,5,6,7): PTR 30:1 — conservative (lowest applicable)
- Policy source: Samagra Shiksha Framework for Implementation (MHRD, 2018)
  inheriting RTE Act 2009 norms for elementary and RMSA norms for secondary
- Computed required_teachers = CEIL(total_enrolment / PTR_norm)
- Computed teacher_gap = GREATEST(required_teachers - total_teachers, 0)
- Added teacher_gap column to teacher_metrics (ALTER TABLE + bootstrap_schema.py)
- Added idx_teacher_school_year index on teacher_metrics (school_id, academic_year)
- Reused existing Phase 2 indexes (idx_yearly_school_year, idx_schools_school_id)
- Batched UPDATE per academic year (~63k rows/batch) for Railway performance
- All computation server-side — no Python row loops
- Idempotent — safe to re-run
- No Phase 2 business logic changed (infrastructure gap engine untouched)
- Updated ai.md with Phase 3 documentation including PTR citations

---

Phase 4 – Composite Compliance Risk Engine

- Implemented weighted composite risk_score formula:
  risk_score = (0.45 × teacher_deficit_ratio) + (0.35 × classroom_deficit_ratio) + (0.20 × growth_scaled)
- Weight justification:
  - 0.45 teacher: RTE Act Section 25 identifies PTR as primary input quality
  - 0.35 classroom: Samagra Shiksha infrastructure norms core capacity constraint
  - 0.20 growth: lagging indicator for demand pressure / decline risk
- Policy alignment: Samagra Shiksha Framework convergent planning mandate
- Deficit ratios capped at 1.0 (prevents outlier distortion)
- Growth capped at 0.50 (filters administrative artefacts)
- Enrolment growth computed via SQL LAG() window function
- Safe division using NULLIF to prevent divide-by-zero
- Risk classification: LOW (0–0.20), MODERATE (0.21–0.50), HIGH (0.51–0.75), CRITICAL (>0.75)
- Schema additions to infrastructure_details:
  classroom_deficit_ratio FLOAT
  teacher_deficit_ratio FLOAT
  enrolment_growth_rate FLOAT
  risk_score FLOAT
  risk_level VARCHAR(20)
- Three batched UPDATE passes per academic year:
  1. Deficit ratios (JOIN teacher_metrics)
  2. Growth rates (LAG() subquery from yearly_metrics)
  3. Composite score + classification (self-UPDATE)
- All computation server-side — no Python row loops
- All four existing indexes reused (no new indexes needed)
- Idempotent — safe to re-run; always overwrites computed columns
- Phase 2 (classroom gap) and Phase 3 (teacher gap) logic unchanged
- Updated ai.md with full policy justification and formula documentation

---

Phase 5 – School Prioritisation Engine

- Created school_priority_index table (one row per school per year)
- State-wide ranking via RANK() OVER (ORDER BY risk_score DESC)
- District-level ranking via RANK() OVER (PARTITION BY district)
- Priority bucketing via PERCENT_RANK() — TOP_5 / TOP_10 / TOP_20 / STANDARD
- Persistent high-risk detection via LAG() — flags schools with 3+ consecutive HIGH/CRITICAL years
- Batched INSERT per academic year (~63k rows/batch)
- Added idx_priority_school_year index
- All computation server-side — no Python row loops
- Idempotent — safe to re-run
- Verified: 437,106 rows; 10,588 persistent high-risk; 22,195 Top 5%
- Updated ai.md with Phase 5 documentation

---

Phase 6 – Budget Allocation Simulator

- Created budget_simulation table
- Seeds classroom_gap + teacher_gap from infrastructure_details + teacher_metrics
- Priority ordering via ROW_NUMBER() — CRITICAL → HIGH → MODERATE → LOW
- Cumulative SUM() OVER() for budget cutoff allocation
- Configurable budget: default ₹50Cr classroom (1,000 rooms @ ₹5L), 10,000 teacher posts
- Tracks classroom_resolved / teacher_resolved per school
- Added idx_budget_school_year and idx_budget_priority indexes
- Batched per academic year
- All computation server-side — no Python row loops
- Idempotent — safe to re-run
- Verified: 7,000 classrooms allocated, 70,000 teachers allocated across 7 years
- Updated ai.md with Phase 6 documentation

---

Phase 7 – Longitudinal Risk Trend Engine

- Created risk_trend table (one row per school per year)
- Risk delta via LAG(risk_score, 1) across full time series
- Trend classification: IMPROVING (<-0.10) / STABLE / DETERIORATING (>+0.10) / BASELINE
- Chronic risk flag: 3+ consecutive HIGH/CRITICAL years (via LAG on risk_level)
- Volatile flag: |risk_delta| > 0.25 in current or previous transition
- Running cumulative average risk via AVG() OVER (ROWS UNBOUNDED PRECEDING)
- Full longitudinal INSERT (all years in single pass for correct LAG windows)
- Chronic + volatile flags batched per year
- Added idx_trend_school_year and idx_trend_direction indexes
- All computation server-side — no Python row loops
- Idempotent — safe to re-run
- Verified: 437,106 rows; 123,487 improving, 75,875 deteriorating, 10,588 chronic
- Updated ai.md with Phase 7 documentation

---

Phase 8 – District Compliance Index

- Created district_compliance_index table (one row per district per year)
- Aggregated: total_schools, avg_risk_score, pct_high_critical, total deficits, total enrolment
- Compliance grading: A (≤0.15) / B (≤0.30) / C (≤0.50) / D (≤0.75) / F (>0.75)
- YoY risk improvement via LAG() on own table
- District ranking via RANK() per year
- Added idx_dci_district_year and idx_dci_rank indexes
- Batched per academic year
- All computation server-side — no Python row loops
- Idempotent — safe to re-run
- Verified: 182 records (26 districts × 7 years); KURNOOL #1 risk (0.3828, Grade C)
- Updated ai.md with Phase 8 documentation

---

Phase 9 – Proposal Validation Engine

- Created school_demand_proposals table (synthetic proposals with CRC32 noise)
- Created proposal_validations table (validated output with decisions)
- CRC32-based deterministic noise (0.7–1.5×) for reproducible proposal simulation
- Multi-dimensional validation against actual classroom_gap and teacher_gap
- Three-tier decision: ACCEPTED / FLAGGED / REJECTED
- Confidence scoring: max(0, 1 − (|1 − cr_ratio| + |1 − tr_ratio|) / 2)
- Reason codes: WITHIN_TOLERANCE, NO_REQUEST, NO_DEFICIT, _\_OVER_REQUEST, _\_UNDER_REQUEST
- Added idx_proposals_school_year, idx_validations_school_year, idx_validations_decision
- Batched per academic year
- All computation server-side — no Python row loops
- Idempotent — safe to re-run
- Verified: 437,106 proposals; 325,758 ACCEPTED, 111,348 FLAGGED; avg confidence 0.916
- Updated ai.md with Phase 9 documentation

---

Phase 10 – Enrolment Forecasting Engine

- Created enrolment_forecast table (3 rows per school — T+1, T+2, T+3)
- Weighted 3-year moving average growth rate via LAG() across full time series
- Growth capped at ±0.30 to filter administrative anomalies
- Projection: E(t+n) = E(t) × (1 + growth)^n for n in {1, 2, 3}
- UDISE+ category-based classroom norms (30/35/40) and PTR norms (30/35)
- Projected classroom and teacher requirements via CEILING(enrolment / norm)
- Projected deficits against current capacity: GREATEST(0, required − current)
- CROSS JOIN with (1, 2, 3) for efficient multi-horizon generation
- Added idx_forecast_school and idx_forecast_year indexes
- All computation server-side — no Python row loops
- Idempotent — safe to re-run
- Verified: 183,951 forecast rows (61,317 schools × 3); base 2024-25 → 2027-28
- Mean growth: −0.1469; T+3 classroom deficit: 247,764; T+3 teacher deficit: 268,040
- Updated ai.md with Phase 10 documentation and system architecture summary
