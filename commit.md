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
