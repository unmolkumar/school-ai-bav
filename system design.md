# System Design Document — School AI BAV

## Andhra Pradesh School Resource Intelligence System

**Version:** 1.0
**Scope:** Comprehensive architecture, data pipeline, computation engines, governance dashboards, and product vision
**Data Source:** UDISE+ (Unified District Information System for Education Plus) — Government of India
**Coverage:** 26 Districts, ~67,000 schools, 7 academic years (2018-19 through 2024-25)
**Database:** MySQL 8.0 (Railway Cloud)
**Runtime:** Python 3.x, SQLAlchemy, pandas

---

# Table of Contents

1. [System Architecture Flowchart](#1-system-architecture-flowchart)
2. [Database Tables — Creation Order](#2-database-tables--creation-order)
3. [Computation Engines — Execution Order](#3-computation-engines--execution-order)
4. [Component Classification Matrix](#4-component-classification-matrix)
5. [Dashboard Design — Multi-Level Governance](#5-dashboard-design--multi-level-governance)
6. [Governance & Decision Workflows](#6-governance--decision-workflows)
7. [Product Vision](#7-product-vision)

---

# 1. System Architecture Flowchart

## 1.1 End-to-End Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    RAW DATA LAYER                                                   │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌──────────────────┐    │
│   │ profile_1   │   │ profile_2   │   │ facility    │   │ teacher     │   │ enrolment_1 & 2  │    │
│   │ .csv        │   │ .csv        │   │ .csv        │   │ .csv        │   │ .csv             │    │
│   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └────────┬─────────┘    │
│          │                 │                 │                 │                    │               │
│          └─────────┬───────┴────────┬────────┴────────┬───────┘                    │               │
│                    ▼                                                               │               │
│          ┌─────────────────┐          LEFT JOINs on school_id                      │               │
│          │ data_preparation │◄─────────────────────────────────────────────────────┘               │
│          │ /load_data.py    │                                                                      │
│          └────────┬────────┘                                                                       │
│                   ▼                                                                                │
│   ┌──────────────────────────────┐                                                                 │
│   │ data/processed/              │   7 per-year master CSVs                                        │
│   │   master_2018-19.csv         │   + 1 longitudinal concat                                       │
│   │   ...                        │                                                                 │
│   │   master_longitudinal.csv    │                                                                 │
│   └──────────────┬───────────────┘                                                                 │
└──────────────────┼─────────────────────────────────────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                  PHASE 1 — SCHEMA & LOAD                                           │
│                                                                                                     │
│   ┌─────────────────────┐        ┌──────────────────────┐                                          │
│   │ bootstrap_schema.py │───────►│ load_master_data.py   │                                         │
│   │ CREATE 4 base tables│        │ CSV → DB (batch 5000) │                                         │
│   └─────────────────────┘        └──────────┬───────────┘                                          │
│                                              │                                                      │
│                    ┌─────────────────────────┬┴───────────────────────────┐                         │
│                    ▼                         ▼                           ▼                          │
│           ┌──────────────┐        ┌──────────────────────┐    ┌──────────────────┐                 │
│           │   schools    │        │ infrastructure_      │    │ teacher_metrics  │                  │
│           │  (67,343)    │        │ details (437,106)     │    │   (437,106)      │                 │
│           └──────────────┘        └──────────────────────┘    └──────────────────┘                 │
│                                   ┌──────────────────────┐                                         │
│                                   │  yearly_metrics      │                                         │
│                                   │   (437,106)          │                                         │
│                                   └──────────────────────┘                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                          PHASE 2–4 — GAP & RISK COMPUTATION                                        │
│                                                                                                     │
│   ┌───────────────────────────┐   ┌───────────────────────────┐   ┌─────────────────────────────┐  │
│   │  Phase 2                  │   │  Phase 3                  │   │  Phase 4                    │  │
│   │  Infrastructure Gap       │──►│  Teacher Adequacy         │──►│  Compliance Risk            │  │
│   │  Engine                   │   │  Engine                   │   │  Engine                     │  │
│   │                           │   │                           │   │                             │  │
│   │  UPDATE infra_details:    │   │  UPDATE teacher_metrics:  │   │  UPDATE infra_details:      │  │
│   │  required_class_rooms     │   │  required_teachers        │   │  teacher_deficit_ratio      │  │
│   │  classroom_gap            │   │  teacher_gap              │   │  classroom_deficit_ratio    │  │
│   │                           │   │                           │   │  enrolment_growth_rate      │  │
│   │  Norm: 30/35/40           │   │  Norm: 30/35              │   │  risk_score (composite)     │  │
│   │  per school_category      │   │  per school_category      │   │  risk_level (4 tiers)       │  │
│   └───────────────────────────┘   └───────────────────────────┘   └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                       PHASE 5–6 — PRIORITISATION & BUDGET SIMULATION                               │
│                                                                                                     │
│   ┌───────────────────────────┐        ┌──────────────────────────────────────┐                     │
│   │  Phase 5                  │        │  Phase 6                             │                     │
│   │  Prioritisation Engine    │───────►│  Budget Allocation Engine            │                     │
│   │                           │        │                                      │                     │
│   │  ► school_priority_index  │        │  ► budget_simulation                 │                     │
│   │    (437,106 rows)         │        │    (437,106 rows)                    │                     │
│   │                           │        │                                      │                     │
│   │  RANK, PERCENT_RANK,      │        │  Classroom @ ₹5L each               │                     │
│   │  priority buckets,        │        │  Teachers @ rank-order               │                     │
│   │  persistent high-risk     │        │  Cumulative allocation               │                     │
│   └───────────────────────────┘        └──────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                      PHASE 7–8 — LONGITUDINAL ANALYTICS                                            │
│                                                                                                     │
│   ┌───────────────────────────┐        ┌──────────────────────────────────────┐                     │
│   │  Phase 7                  │        │  Phase 8                             │                     │
│   │  Risk Trend Engine        │        │  District Compliance Index           │                     │
│   │                           │        │                                      │                     │
│   │  ► risk_trend             │        │  ► district_compliance_index         │                     │
│   │    (437,106 rows)         │        │    (182 rows = 26 × 7)              │                     │
│   │                           │        │                                      │                     │
│   │  LAG-based trend detect   │        │  District aggregates, grades A–F     │                     │
│   │  chronic / volatile flags │        │  YoY Δ, state rank                   │                     │
│   └───────────────────────────┘        └──────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                   PHASE 9–10 — SIMULATION & FORECASTING                                            │
│                                                                                                     │
│   ┌───────────────────────────┐        ┌──────────────────────────────────────┐                     │
│   │  Phase 9                  │        │  Phase 10                            │                     │
│   │  Proposal Validation      │        │  Forecasting Engine                  │                     │
│   │                           │        │                                      │                     │
│   │  ► school_demand_proposals│        │  ► enrolment_forecast                │                     │
│   │    (437,106 rows)         │        │    (183,951 rows = 61,317 × 3)      │                     │
│   │  ► proposal_validations   │        │                                      │                     │
│   │    (437,106 rows)         │        │  Weighted moving-avg growth          │                     │
│   │                           │        │  T+1, T+2, T+3 projections           │                     │
│   │  CRC32 noise simulation   │        │  Future gap extrapolation            │                     │
│   │  Rule-based validation    │        │                                      │                     │
│   └───────────────────────────┘        └──────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              DASHBOARD & GOVERNANCE LAYER                                           │
│                                                                                                     │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                           │
│   │ STATE-LEVEL  │  │ DISTRICT-    │  │ BLOCK-LEVEL  │  │ SCHOOL-LEVEL │                           │
│   │ DASHBOARD    │  │ LEVEL        │  │ DASHBOARD    │  │ DASHBOARD    │                           │
│   │              │  │ DASHBOARD    │  │              │  │              │                           │
│   │ Aggregate    │  │ Compliance   │  │ Block-wise   │  │ Individual   │                           │
│   │ risk map,    │  │ grades,      │  │ gaps, school  │  │ risk card,   │                           │
│   │ forecasts,   │  │ rankings,    │  │ listings,     │  │ proposals,   │                           │
│   │ budget       │  │ trend lines  │  │ trend charts  │  │ forecast     │                           │
│   └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘                           │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 1.2 Engine Dependency Graph

```
                     ┌──────────────────┐
                     │  Raw CSV Data     │
                     │  (UDISE+ Portal)  │
                     └────────┬─────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │  data_preparation │
                     │  /load_data.py    │
                     └────────┬─────────┘
                              │
                              ▼
              ┌──────────────────────────────┐
              │  Phase 1 — Schema Bootstrap   │
              │  + Master Data Loader         │
              │                               │
              │  Tables: schools,             │
              │  yearly_metrics,              │
              │  infrastructure_details,      │
              │  teacher_metrics              │
              └──────────────┬───────────────┘
                             │
              ┌──────────────┴───────────────┐
              ▼                              ▼
   ┌─────────────────────┐      ┌─────────────────────┐
   │  Phase 2             │      │  Phase 3             │
   │  Infrastructure Gap  │      │  Teacher Adequacy    │
   │  (UPDATEs infra)     │      │  (UPDATEs teacher)   │
   └──────────┬──────────┘      └──────────┬──────────┘
              │                             │
              └──────────────┬──────────────┘
                             │  Both must complete
                             ▼
              ┌──────────────────────────────┐
              │  Phase 4 — Compliance Risk    │
              │  (UPDATEs 5 columns on infra) │
              │  Reads: infra + teacher +      │
              │         yearly_metrics         │
              └──────────────┬───────────────┘
                             │
              ┌──────────────┴───────────────┐
              ▼                              ▼
   ┌─────────────────────┐      ┌─────────────────────┐
   │  Phase 5             │      │  Phase 7             │
   │  Prioritisation      │      │  Risk Trend          │
   │  (NEW table)         │      │  (NEW table)         │
   └──────────┬──────────┘      └─────────────────────┘
              │
              ▼
   ┌─────────────────────┐      ┌─────────────────────┐
   │  Phase 6             │      │  Phase 8             │
   │  Budget Allocation   │      │  District Compliance │
   │  (NEW table)         │      │  (NEW table)         │
   └─────────────────────┘      └─────────────────────┘

   ┌─────────────────────┐      ┌─────────────────────┐
   │  Phase 9             │      │  Phase 10            │
   │  Proposal Validation │      │  Forecasting         │
   │  (2 NEW tables)      │      │  (NEW table)         │
   └─────────────────────┘      └─────────────────────┘
```

### Dependency Rules

| Engine                        | Hard Prerequisites      | Reads From                                                               |
| ----------------------------- | ----------------------- | ------------------------------------------------------------------------ |
| Phase 2 — Infrastructure Gap  | Phase 1 (schema + load) | `infrastructure_details`, `yearly_metrics`, `schools`                    |
| Phase 3 — Teacher Adequacy    | Phase 1 (schema + load) | `teacher_metrics`, `yearly_metrics`, `schools`                           |
| Phase 4 — Compliance Risk     | Phase 2 AND Phase 3     | `infrastructure_details`, `teacher_metrics`, `yearly_metrics`            |
| Phase 5 — Prioritisation      | Phase 4                 | `infrastructure_details`, `teacher_metrics`, `schools`                   |
| Phase 6 — Budget Allocation   | Phase 5                 | `school_priority_index`, `infrastructure_details`, `teacher_metrics`     |
| Phase 7 — Risk Trend          | Phase 4                 | `infrastructure_details`                                                 |
| Phase 8 — District Compliance | Phase 4                 | `infrastructure_details`, `schools`                                      |
| Phase 9 — Proposal Validation | Phase 2 AND Phase 3     | `infrastructure_details`, `teacher_metrics`                              |
| Phase 10 — Forecasting        | Phase 2 AND Phase 3     | `yearly_metrics`, `infrastructure_details`, `teacher_metrics`, `schools` |

---

# 2. Database Tables — Creation Order

## 2.1 Table: `schools` (Dimension)

**Created by:** Phase 1 — `bootstrap_schema.py` + `load_master_data.py`
**Purpose:** Master dimension table holding one row per unique school across all years. Stores immutable identity and location attributes. When a school appears in multiple years, the **latest year's** data wins (deduplication via `sort_values(year, ascending=False).drop_duplicates(school_id, keep='first')`).
**Row Count:** 67,343

| Column            | Type                | Source                                                | Classification    |
| ----------------- | ------------------- | ----------------------------------------------------- | ----------------- |
| `school_id`       | VARCHAR(50), **PK** | CSV `school_id` (originally `pseudocode` from UDISE+) | Raw               |
| `school_name`     | VARCHAR(255)        | Not available in current CSV — NULL                   | Raw (placeholder) |
| `district`        | VARCHAR(100)        | CSV `district`                                        | Raw               |
| `block`           | VARCHAR(100)        | CSV `block`                                           | Raw               |
| `management_type` | VARCHAR(100)        | CSV `managment` (original spelling)                   | Raw               |
| `school_category` | VARCHAR(100)        | CSV `school_category` (UDISE+ codes 1–11)             | Raw               |
| `latitude`        | FLOAT               | Not available — NULL                                  | Raw (placeholder) |
| `longitude`       | FLOAT               | Not available — NULL                                  | Raw (placeholder) |

**Relationships:** Referenced by every other table via `school_id`.

**UDISE+ School Category Codes:**

| Code | Description                                                           | Level                     |
| ---- | --------------------------------------------------------------------- | ------------------------- |
| 1    | Primary only (I–V)                                                    | Primary                   |
| 2    | Primary with Upper Primary (I–VIII)                                   | Primary + Upper Primary   |
| 3    | Primary with Upper Primary, Secondary and Higher Secondary (I–XII)    | All                       |
| 4    | Upper Primary only (VI–VIII)                                          | Upper Primary             |
| 5    | Upper Primary with Secondary and Higher Secondary (VI–XII)            | Upper Primary +           |
| 6    | Primary with Upper Primary and Secondary (I–X)                        | Up to Secondary           |
| 7    | Upper Primary with Secondary (VI–X)                                   | Upper Primary + Secondary |
| 8    | Secondary only (IX–X)                                                 | Secondary                 |
| 9    | Secondary with Higher Secondary (IX–XII)                              | Secondary +               |
| 10   | Higher Secondary only (XI–XII)                                        | Higher Secondary          |
| 11   | Primary with Upper Primary and Secondary and Higher Secondary (I–XII) | All (alias of 3)          |

---

## 2.2 Table: `yearly_metrics` (Fact)

**Created by:** Phase 1 — `bootstrap_schema.py` + `load_master_data.py`
**Purpose:** Stores annual enrolment figures per school-year. One row per school per academic year. This is the enrolment fact table that feeds gap computations and growth rate calculations.
**Row Count:** 437,106 (~63k schools × 7 years)

| Column            | Type                        | Source                                                  | Classification                                      |
| ----------------- | --------------------------- | ------------------------------------------------------- | --------------------------------------------------- |
| `id`              | INT, **PK**, AUTO_INCREMENT | System generated                                        | System                                              |
| `school_id`       | VARCHAR(50)                 | CSV `school_id`                                         | Raw                                                 |
| `academic_year`   | VARCHAR(20)                 | CSV `year` (e.g., `"2024-25"`)                          | Raw                                                 |
| `total_enrolment` | INT                         | CSV `total_enrolment` (sum of all grade-gender columns) | Derived (aggregated from ~100 gender×grade columns) |
| `attendance_rate` | FLOAT                       | Not available — NULL                                    | Raw (placeholder)                                   |

**Relationships:** Joined to `infrastructure_details` and `teacher_metrics` via `(school_id, academic_year)`.

---

## 2.3 Table: `infrastructure_details` (Fact + Computed)

**Created by:** Phase 1 — `bootstrap_schema.py` + `load_master_data.py`
**Modified by:** Phase 2 (Infrastructure Gap Engine) — adds `required_class_rooms`, `classroom_gap`
**Modified by:** Phase 4 (Compliance Risk Engine) — adds 5 risk columns
**Purpose:** Central fact table for infrastructure. Starts with raw facility data from UDISE+, then enriched with computed gap and risk metrics by downstream engines. This table carries the most columns and serves as the primary analytical surface.
**Row Count:** 437,106

### Raw Columns (loaded from CSV)

| Column                      | Type                        | Source                                                                | Classification    |
| --------------------------- | --------------------------- | --------------------------------------------------------------------- | ----------------- |
| `id`                        | INT, **PK**, AUTO_INCREMENT | System generated                                                      | System            |
| `school_id`                 | VARCHAR(50)                 | CSV `school_id`                                                       | Raw               |
| `academic_year`             | VARCHAR(20)                 | CSV `year`                                                            | Raw               |
| `total_class_rooms`         | INT                         | CSV `total_class_rooms`                                               | Raw               |
| `usable_class_rooms`        | INT                         | CSV `classrooms_in_good_condition`                                    | Raw               |
| `classroom_condition_score` | INT                         | `(needs_major_repair × 2) + (needs_minor_repair × 1)`                 | Derived           |
| `drinking_water_available`  | BOOLEAN                     | CSV `drinking_water_available` (1=Yes, 2=No)                          | Raw (recoded)     |
| `electricity_available`     | BOOLEAN                     | CSV `electricity_availability` (1=Yes, 2=No)                          | Raw (recoded)     |
| `internet_available`        | BOOLEAN                     | CSV `internet` (1=Yes, 2=No)                                          | Raw (recoded)     |
| `separate_girls_toilet`     | BOOLEAN                     | CSV `separate_girls_toilet` (1=Yes, 2=No)                             | Raw (recoded)     |
| `cwsn_toilet_available`     | BOOLEAN                     | `True` if `func_boys_cwsn_friendly=1` OR `func_girls_cwsn_friendly=1` | Derived           |
| `ramp_available`            | BOOLEAN                     | CSV `availability_ramps` (1=Yes, 2=No)                                | Raw (recoded)     |
| `resource_room_available`   | BOOLEAN                     | CSV `resource_room_available` (1=Yes, 2=No)                           | Raw (recoded)     |
| `building_condition`        | VARCHAR(50)                 | CSV `building_status`                                                 | Raw               |
| `last_major_repair_year`    | INT                         | Not available — NULL                                                  | Raw (placeholder) |

### Computed Columns — Phase 2 (Infrastructure Gap Engine)

| Column                 | Type | Formula                                                  | Classification |
| ---------------------- | ---- | -------------------------------------------------------- | -------------- |
| `required_class_rooms` | INT  | `CEIL(total_enrolment / classroom_norm)`                 | Norm-based     |
| `classroom_gap`        | INT  | `GREATEST(required_class_rooms - usable_class_rooms, 0)` | Derived        |

### Computed Columns — Phase 4 (Compliance Risk Engine)

| Column                    | Type        | Formula                                                                  | Classification     |
| ------------------------- | ----------- | ------------------------------------------------------------------------ | ------------------ |
| `teacher_deficit_ratio`   | FLOAT       | `LEAST(1.0, teacher_gap / GREATEST(required_teachers, 1))`               | Statistical ratio  |
| `classroom_deficit_ratio` | FLOAT       | `LEAST(1.0, classroom_gap / GREATEST(required_class_rooms, 1))`          | Statistical ratio  |
| `enrolment_growth_rate`   | FLOAT       | `(enrolment - LAG(enrolment)) / LAG(enrolment)`                          | Statistical (YoY)  |
| `risk_score`              | FLOAT       | `0.45 × teacher_deficit + 0.35 × classroom_deficit + 0.20 × ABS(growth)` | Composite weighted |
| `risk_level`              | VARCHAR(20) | Thresholded from risk_score (see Phase 4 engine)                         | Rule-based         |

**Indexes:**

| Index Name              | Columns                       | Purpose                       |
| ----------------------- | ----------------------------- | ----------------------------- |
| `idx_infra_school_year` | `(school_id, academic_year)`  | Fast lookup for gap/risk join |
| `idx_infra_risk_level`  | `(academic_year, risk_level)` | Filter by risk tier           |

---

## 2.4 Table: `teacher_metrics` (Fact + Computed)

**Created by:** Phase 1 — `bootstrap_schema.py` + `load_master_data.py`
**Modified by:** Phase 3 (Teacher Adequacy Engine) — adds `required_teachers`, `teacher_gap`
**Purpose:** Teacher staffing fact table. Raw `total_teachers` from UDISE+ enriched with PTR-based adequacy computations.
**Row Count:** 437,106

| Column              | Type                        | Source / Formula                                           | Classification |
| ------------------- | --------------------------- | ---------------------------------------------------------- | -------------- |
| `id`                | INT, **PK**, AUTO_INCREMENT | System generated                                           | System         |
| `school_id`         | VARCHAR(50)                 | CSV `school_id`                                            | Raw            |
| `academic_year`     | VARCHAR(20)                 | CSV `year`                                                 | Raw            |
| `total_teachers`    | INT                         | CSV `total_tch` or `total_teacher` (schema drift handling) | Raw            |
| `required_teachers` | INT                         | `CEIL(total_enrolment / ptr_norm)`                         | Norm-based     |
| `teacher_gap`       | INT                         | `GREATEST(required_teachers - total_teachers, 0)`          | Derived        |

**Note on schema drift:** UDISE+ changed the column name from `total_tch` to `total_teacher` starting 2022-23. The loader handles both.

**Indexes:**

| Index Name                | Columns                      | Purpose                       |
| ------------------------- | ---------------------------- | ----------------------------- |
| `idx_teacher_school_year` | `(school_id, academic_year)` | Fast lookup for gap/risk join |

---

## 2.5 Table: `school_priority_index` (Derived)

**Created by:** Phase 5 — Prioritisation Engine
**Purpose:** Ranks every school-year record by risk severity using statistical window functions. Assigns priority buckets for resource allocation ordering. Identifies schools with persistent multi-year high risk.
**Row Count:** 437,106

| Column                 | Type                        | Formula / Source                                                            | Classification             |
| ---------------------- | --------------------------- | --------------------------------------------------------------------------- | -------------------------- |
| `id`                   | INT, **PK**, AUTO_INCREMENT | System generated                                                            | System                     |
| `school_id`            | VARCHAR(50)                 | From `infrastructure_details`                                               | Raw                        |
| `academic_year`        | VARCHAR(20)                 | From `infrastructure_details`                                               | Raw                        |
| `risk_score`           | FLOAT                       | Copied from `infrastructure_details.risk_score`                             | Composite weighted         |
| `risk_rank`            | INT                         | `RANK() OVER (PARTITION BY academic_year ORDER BY risk_score DESC)`         | Statistical (rank)         |
| `percentile`           | FLOAT                       | `PERCENT_RANK() OVER (PARTITION BY academic_year ORDER BY risk_score DESC)` | Statistical (percentile)   |
| `priority_bucket`      | VARCHAR(20)                 | Thresholded from percentile (see below)                                     | Rule-based                 |
| `persistent_high_risk` | BOOLEAN                     | `True` if LAG(risk_level, 1) AND LAG(risk_level, 2) are both CRITICAL/HIGH  | Statistical (longitudinal) |

**Priority Bucket Thresholds:**

| Bucket     | Condition                | Meaning                     |
| ---------- | ------------------------ | --------------------------- |
| `TOP_5`    | percentile < 0.05        | Worst 5% of schools by risk |
| `TOP_10`   | 0.05 ≤ percentile < 0.10 | Next 5% (worst 5–10%)       |
| `TOP_20`   | 0.10 ≤ percentile < 0.20 | Next 10% (worst 10–20%)     |
| `STANDARD` | percentile ≥ 0.20        | Remaining 80%               |

**Persistent High-Risk Logic:**

```
persistent_high_risk = TRUE when:
  - LAG(risk_level, 1) IN ('CRITICAL', 'HIGH')
  - AND LAG(risk_level, 2) IN ('CRITICAL', 'HIGH')
  - i.e., school has been CRITICAL or HIGH for 3 consecutive years
```

**Indexes:**

| Index Name                 | Columns                                 |
| -------------------------- | --------------------------------------- |
| `idx_priority_school_year` | `(school_id, academic_year)`            |
| `idx_priority_bucket`      | `(academic_year, priority_bucket)`      |
| `idx_priority_persistent`  | `(academic_year, persistent_high_risk)` |

---

## 2.6 Table: `budget_simulation` (Simulation)

**Created by:** Phase 6 — Budget Allocation Engine
**Purpose:** Simulates constrained budget allocation under a fixed annual envelope. Determines which schools receive classroom construction funding and teacher postings based on risk-priority ordering.
**Row Count:** 437,106

| Column                 | Type                        | Formula / Source                                        | Classification |
| ---------------------- | --------------------------- | ------------------------------------------------------- | -------------- |
| `id`                   | INT, **PK**, AUTO_INCREMENT | System generated                                        | System         |
| `school_id`            | VARCHAR(50)                 | From priority index                                     | Raw            |
| `academic_year`        | VARCHAR(20)                 | From priority index                                     | Raw            |
| `risk_rank`            | INT                         | From `school_priority_index.risk_rank`                  | Statistical    |
| `priority_bucket`      | VARCHAR(20)                 | From `school_priority_index.priority_bucket`            | Rule-based     |
| `classroom_gap`        | INT                         | From `infrastructure_details.classroom_gap`             | Derived        |
| `teacher_gap`          | INT                         | From `teacher_metrics.teacher_gap`                      | Derived        |
| `classrooms_allocated` | INT                         | Allocation result (0 or classroom_gap if within budget) | Simulation     |
| `teachers_allocated`   | INT                         | Allocation result (0 or teacher_gap if within budget)   | Simulation     |
| `estimated_cost`       | FLOAT                       | `classrooms_allocated × ₹500,000`                       | Simulation     |
| `allocation_status`    | VARCHAR(20)                 | `FUNDED` / `PARTIALLY_FUNDED` / `UNFUNDED`              | Simulation     |
| `cumulative_cost`      | FLOAT                       | Running total of estimated_cost in priority order       | Simulation     |

**Budget Constants:**

| Parameter                  | Value                     | Rationale                                    |
| -------------------------- | ------------------------- | -------------------------------------------- |
| Annual classroom budget    | ₹50,00,00,000 (₹50 Crore) | State-level annual infrastructure allocation |
| Cost per classroom         | ₹5,00,000 (₹5 Lakh)       | SSA/PM SHRI construction norm                |
| Max classrooms from budget | 7,000 per year            | ₹50Cr ÷ ₹5L                                  |
| Max teacher postings       | 10,000 per year           | State recruitment capacity                   |

**Allocation Algorithm:**

```
1. ORDER schools by risk_rank ASC (highest-risk first)
2. Cumulative classroom fill:
     cumulative_classrooms = SUM(classroom_gap) OVER (ORDER BY risk_rank)
     classrooms_allocated  = classroom_gap   WHERE cumulative ≤ 7,000
                           = 0               WHERE cumulative > 7,000
3. Cumulative teacher fill:
     cumulative_teachers   = SUM(teacher_gap) OVER (ORDER BY risk_rank)
     teachers_allocated    = teacher_gap     WHERE cumulative ≤ 10,000
                           = 0               WHERE cumulative > 10,000
4. Allocation status:
     FUNDED           = both classrooms AND teachers allocated (gap > 0)
     PARTIALLY_FUNDED = only one dimension allocated
     UNFUNDED         = nothing allocated
```

**Indexes:**

| Index Name               | Columns                              |
| ------------------------ | ------------------------------------ |
| `idx_budget_school_year` | `(school_id, academic_year)`         |
| `idx_budget_status`      | `(academic_year, allocation_status)` |

---

## 2.7 Table: `risk_trend` (Derived — Longitudinal)

**Created by:** Phase 7 — Risk Trend Engine
**Purpose:** Tracks directional change in each school's risk score over time. Classifies schools as improving/stable/deteriorating compared to prior year. Flags chronic (persistently high) and volatile (large swings) patterns.
**Row Count:** 437,106

| Column            | Type                        | Formula / Source                                                          | Classification             |
| ----------------- | --------------------------- | ------------------------------------------------------------------------- | -------------------------- |
| `id`              | INT, **PK**, AUTO_INCREMENT | System generated                                                          | System                     |
| `school_id`       | VARCHAR(50)                 | From `infrastructure_details`                                             | Raw                        |
| `academic_year`   | VARCHAR(20)                 | From `infrastructure_details`                                             | Raw                        |
| `risk_score`      | FLOAT                       | From `infrastructure_details.risk_score`                                  | Composite weighted         |
| `prev_risk_score` | FLOAT                       | `LAG(risk_score, 1) OVER (PARTITION BY school_id ORDER BY academic_year)` | Statistical (lag)          |
| `risk_delta`      | FLOAT                       | `risk_score - prev_risk_score`                                            | Derived                    |
| `trend_direction` | VARCHAR(20)                 | Thresholded from risk_delta (see below)                                   | Rule-based                 |
| `is_chronic`      | BOOLEAN                     | `True` if HIGH/CRITICAL for 3+ consecutive years                          | Statistical (longitudinal) |
| `is_volatile`     | BOOLEAN                     | `True` if ABS(risk_delta) > 0.15`                                         | Statistical (threshold)    |

**Trend Direction Thresholds:**

| Direction       | Condition                              | Meaning                          |
| --------------- | -------------------------------------- | -------------------------------- |
| `BASELINE`      | `prev_risk_score IS NULL` (first year) | No prior data to compare         |
| `IMPROVING`     | `risk_delta < -0.05`                   | Risk dropped by more than 0.05   |
| `STABLE`        | `-0.05 ≤ risk_delta ≤ 0.05`            | Risk stayed within ±0.05 band    |
| `DETERIORATING` | `risk_delta > 0.05`                    | Risk increased by more than 0.05 |

**Chronic Flag Logic:**

```
is_chronic = TRUE when:
  - Current risk_level IN ('CRITICAL', 'HIGH')
  - AND LAG(risk_level, 1) IN ('CRITICAL', 'HIGH')
  - AND LAG(risk_level, 2) IN ('CRITICAL', 'HIGH')
  → School has been high/critical for at least 3 consecutive years
```

**Indexes:**

| Index Name              | Columns                            |
| ----------------------- | ---------------------------------- |
| `idx_trend_school_year` | `(school_id, academic_year)`       |
| `idx_trend_direction`   | `(academic_year, trend_direction)` |
| `idx_trend_chronic`     | `(academic_year, is_chronic)`      |

---

## 2.8 Table: `district_compliance_index` (Aggregated)

**Created by:** Phase 8 — District Compliance Index Engine
**Purpose:** Aggregates school-level risk data to the district level. Provides annual compliance grades, year-over-year progress tracking, and state-wide ranking for district administrators.
**Row Count:** 182 (26 districts × 7 years)

| Column             | Type                        | Formula / Source                                              | Classification     |
| ------------------ | --------------------------- | ------------------------------------------------------------- | ------------------ |
| `id`               | INT, **PK**, AUTO_INCREMENT | System generated                                              | System             |
| `district`         | VARCHAR(100)                | From `schools.district`                                       | Raw                |
| `academic_year`    | VARCHAR(20)                 | From `infrastructure_details.academic_year`                   | Raw                |
| `total_schools`    | INT                         | `COUNT(DISTINCT school_id)` in district-year                  | Aggregated         |
| `avg_risk_score`   | FLOAT                       | `AVG(risk_score)` across district's schools                   | Aggregated         |
| `pct_critical`     | FLOAT                       | `% of schools with risk_level = 'CRITICAL'`                   | Aggregated         |
| `pct_high`         | FLOAT                       | `% of schools with risk_level = 'HIGH'`                       | Aggregated         |
| `pct_moderate`     | FLOAT                       | `% of schools with risk_level = 'MODERATE'`                   | Aggregated         |
| `pct_low`          | FLOAT                       | `% of schools with risk_level = 'LOW'`                        | Aggregated         |
| `compliance_grade` | VARCHAR(2)                  | Graded from avg_risk_score (see below)                        | Rule-based         |
| `yoy_risk_change`  | FLOAT                       | `avg_risk_score - LAG(avg_risk_score)`                        | Statistical (YoY)  |
| `state_rank`       | INT                         | `RANK() OVER (PARTITION BY year ORDER BY avg_risk_score ASC)` | Statistical (rank) |

**Compliance Grade Thresholds:**

| Grade | Condition                      | Meaning                       |
| ----- | ------------------------------ | ----------------------------- |
| A     | `avg_risk_score < 0.15`        | Excellent — minimal risk      |
| B     | `0.15 ≤ avg_risk_score < 0.30` | Good — manageable risk        |
| C     | `0.30 ≤ avg_risk_score < 0.50` | Fair — attention needed       |
| D     | `0.50 ≤ avg_risk_score < 0.70` | Poor — significant gaps       |
| F     | `avg_risk_score ≥ 0.70`        | Failing — urgent intervention |

**Current Data Distribution:** B = 96 records, C = 86 records. No A, D, or F grades exist in the dataset — districts cluster in the moderate-to-good range.

**Indexes:**

| Index Name              | Columns                             |
| ----------------------- | ----------------------------------- |
| `idx_dci_district_year` | `(district, academic_year)`         |
| `idx_dci_grade`         | `(academic_year, compliance_grade)` |

---

## 2.9 Table: `school_demand_proposals` (Simulation)

**Created by:** Phase 9 — Proposal Validation Engine
**Purpose:** Simulates resource demand proposals that schools would submit. Uses deterministic noise (CRC32) to generate realistic but reproducible request quantities that deviate from actual gaps. This creates a test bed for the validation engine.
**Row Count:** 437,106

| Column                 | Type                        | Formula / Source                           | Classification |
| ---------------------- | --------------------------- | ------------------------------------------ | -------------- |
| `id`                   | INT, **PK**, AUTO_INCREMENT | System generated                           | System         |
| `school_id`            | VARCHAR(50)                 | From `infrastructure_details`              | Raw            |
| `academic_year`        | VARCHAR(20)                 | From `infrastructure_details`              | Raw            |
| `classrooms_requested` | INT                         | `classroom_gap × noise_factor` (see below) | Simulation     |
| `teachers_requested`   | INT                         | `teacher_gap × noise_factor` (see below)   | Simulation     |

**Noise Factor Formula (deterministic per school-year):**

```
noise_factor = 0.7 + (CRC32(CONCAT(school_id, academic_year, salt)) MOD 80) / 100.0

Range: 0.70 to 1.49
Salt: 'cr' for classrooms, 'tr' for teachers
```

This produces repeatable "realistic" proposals where some schools over-request (factor > 1.0) and some under-request (factor < 1.0) relative to their actual gap.

**Formula:**

```sql
classrooms_requested = GREATEST(0, ROUND(
    CASE WHEN classroom_gap > 0 THEN classroom_gap ELSE 0 END
    × (0.7 + (CRC32(CONCAT(school_id, academic_year, 'cr')) MOD 80) / 100.0)
))
```

**Indexes:**

| Index Name                  | Columns                      |
| --------------------------- | ---------------------------- |
| `idx_proposals_school_year` | `(school_id, academic_year)` |

---

## 2.10 Table: `proposal_validations` (Derived — Rule-based)

**Created by:** Phase 9 — Proposal Validation Engine
**Purpose:** Validates each synthetic proposal against actual infrastructure and teacher gaps. Produces decision status (ACCEPTED/FLAGGED/REJECTED), reason codes, and confidence scores. Demonstrates how an automated validation system would catch over-requests, under-requests, and fraudulent claims.
**Row Count:** 437,106

| Column                 | Type                        | Formula / Source                                    | Classification    |
| ---------------------- | --------------------------- | --------------------------------------------------- | ----------------- |
| `id`                   | INT, **PK**, AUTO_INCREMENT | System generated                                    | System            |
| `school_id`            | VARCHAR(50)                 | From proposals                                      | Raw               |
| `academic_year`        | VARCHAR(20)                 | From proposals                                      | Raw               |
| `classrooms_requested` | INT                         | From `school_demand_proposals`                      | Simulation        |
| `teachers_requested`   | INT                         | From `school_demand_proposals`                      | Simulation        |
| `classroom_gap`        | INT                         | From `infrastructure_details` (actual gap)          | Derived           |
| `teacher_gap`          | INT                         | From `teacher_metrics` (actual gap)                 | Derived           |
| `classroom_ratio`      | FLOAT                       | `classrooms_requested / GREATEST(classroom_gap, 1)` | Statistical ratio |
| `teacher_ratio`        | FLOAT                       | `teachers_requested / GREATEST(teacher_gap, 1)`     | Statistical ratio |
| `decision_status`      | VARCHAR(20)                 | Rule-based validation result                        | Rule-based        |
| `reason_code`          | VARCHAR(50)                 | Specific reason for the decision                    | Rule-based        |
| `confidence_score`     | FLOAT                       | `1.0 - (ABS(1 - cr_ratio) + ABS(1 - tr_ratio)) / 2` | Statistical       |

**Decision Rules:**

| Decision   | Condition                           | Reason Code                                          |
| ---------- | ----------------------------------- | ---------------------------------------------------- |
| `REJECTED` | No deficit but requests resources   | `NO_DEFICIT`                                         |
| `REJECTED` | ratio > 1.50 on either dimension    | `CLASSROOM_OVER_REQUEST` or `TEACHER_OVER_REQUEST`   |
| `FLAGGED`  | ratio 1.20–1.50 on either dimension | `CLASSROOM_MODERATE_OVER` or `TEACHER_MODERATE_OVER` |
| `FLAGGED`  | ratio < 0.50 on either dimension    | `CLASSROOM_UNDER_REQUEST` or `TEACHER_UNDER_REQUEST` |
| `ACCEPTED` | ratio 0.50–1.20 on both dimensions  | `WITHIN_TOLERANCE`                                   |
| `ACCEPTED` | No request and no gap               | `NO_REQUEST`                                         |

**Confidence Score Formula:**

$$\text{confidence} = \max\!\Big(0,\; 1 - \frac{|1 - r_{\text{cr}}| + |1 - r_{\text{tr}}|}{2}\Big)$$

Where $r_{\text{cr}}$ = classroom ratio, $r_{\text{tr}}$ = teacher ratio. A perfect match (ratio = 1.0 on both) yields confidence = 1.0.

**Current Data:** 325,758 ACCEPTED (74.5%), 111,348 FLAGGED (25.5%), 0 REJECTED. Average confidence = 0.916.

**Indexes:**

| Index Name                    | Columns                            |
| ----------------------------- | ---------------------------------- |
| `idx_validations_school_year` | `(school_id, academic_year)`       |
| `idx_validations_decision`    | `(academic_year, decision_status)` |

---

## 2.11 Table: `enrolment_forecast` (Forecasted)

**Created by:** Phase 10 — Forecasting Engine
**Purpose:** Projects future enrolment, classroom requirements, and teacher requirements for T+1, T+2, and T+3 years using a weighted moving average growth model. Enables proactive planning by showing where gaps will grow if no intervention occurs.
**Row Count:** 183,951 (61,317 schools × 3 forecast horizons)

| Column                     | Type                        | Formula / Source                                                 | Classification      |
| -------------------------- | --------------------------- | ---------------------------------------------------------------- | ------------------- |
| `id`                       | INT, **PK**, AUTO_INCREMENT | System generated                                                 | System              |
| `school_id`                | VARCHAR(50)                 | From source tables                                               | Raw                 |
| `base_year`                | VARCHAR(20)                 | `MAX(academic_year)` from `yearly_metrics` (currently "2024-25") | Raw                 |
| `forecast_year`            | VARCHAR(20)                 | Computed string (e.g., "2025-26", "2026-27", "2027-28")          | Derived             |
| `years_ahead`              | INT                         | 1, 2, or 3                                                       | System              |
| `base_enrolment`           | INT                         | Enrolment in base_year                                           | Raw                 |
| `avg_growth_rate`          | FLOAT                       | Weighted moving average of 3 prior year deltas                   | Statistical         |
| `projected_enrolment`      | INT                         | `base_enrolment × (1 + capped_growth)^years_ahead`               | Forecasted          |
| `projected_classrooms_req` | INT                         | `CEIL(projected_enrolment / classroom_norm)`                     | Norm-based forecast |
| `projected_teachers_req`   | INT                         | `CEIL(projected_enrolment / ptr_norm)`                           | Norm-based forecast |
| `current_classrooms`       | INT                         | From latest `infrastructure_details.usable_class_rooms`          | Raw                 |
| `current_teachers`         | INT                         | From latest `teacher_metrics.total_teachers`                     | Raw                 |
| `projected_classroom_gap`  | INT                         | `GREATEST(0, projected_classrooms_req - current_classrooms)`     | Forecasted          |
| `projected_teacher_gap`    | INT                         | `GREATEST(0, projected_teachers_req - current_teachers)`         | Forecasted          |
| `school_category`          | INT                         | From `schools.school_category`                                   | Raw                 |

**Growth Rate Formula — Weighted Moving Average (3-year window):**

$$g = \frac{3 \cdot \Delta_1 + 2 \cdot \Delta_2 + 1 \cdot \Delta_3}{6 \cdot E_{t-1}}$$

Where:

- $\Delta_1 = E_t - E_{t-1}$ (most recent year-over-year change, weight = 3)
- $\Delta_2 = E_{t-1} - E_{t-2}$ (prior year change, weight = 2)
- $\Delta_3 = E_{t-2} - E_{t-3}$ (earliest year change, weight = 1)
- $E_t$ = total enrolment in year $t$

**Capping:** Growth rate is capped at $[-0.30, +0.30]$ to prevent runaway projections.

**Projection Formula:**

$$\hat{E}_{t+k} = \max\!\Big(0,\; \text{round}\big(E_t \cdot (1 + g_{\text{capped}})^k\big)\Big)$$

Where $k \in \{1, 2, 3\}$.

**Classroom and Teacher Norms (identical to Phase 2/3):**

| school_category    | Classroom Norm (students/room) | PTR Norm (students/teacher) |
| ------------------ | ------------------------------ | --------------------------- |
| 1, 2, 3            | 30                             | 30                          |
| 4, 5               | 35                             | 30                          |
| 6, 7, 8, 9, 10, 11 | 40                             | 35                          |

**Cross-Join Generation:** Each school produces 3 rows (T+1, T+2, T+3) via:

```sql
CROSS JOIN (SELECT 1 AS years_ahead UNION ALL SELECT 2 UNION ALL SELECT 3) gen
```

**Current Forecast Results:**

| Horizon       | Projected Classroom Gap | Projected Teacher Gap |
| ------------- | ----------------------- | --------------------- |
| T+1 (2025-26) | 200,719                 | 209,829               |
| T+2 (2026-27) | 218,586                 | 232,862               |
| T+3 (2027-28) | 247,764                 | 268,040               |

Mean growth rate: -0.1469 (net declining enrolment across AP — consistent with demographic trends).

**Indexes:**

| Index Name            | Columns                        |
| --------------------- | ------------------------------ |
| `idx_forecast_school` | `(school_id, base_year)`       |
| `idx_forecast_year`   | `(forecast_year, years_ahead)` |

---

# 3. Computation Engines — Execution Order

## 3.1 Phase 2 — Infrastructure Gap Engine

**File:** `engines/infrastructure_gap_engine.py`
**Type:** Norm-based computation
**Operation:** UPDATE (modifies `infrastructure_details` in-place)
**Rows Affected:** 437,106
**Execution Time:** ~7 years × batch UPDATE

### What It Does

Computes how many classrooms each school **should** have based on UDISE+ student-per-classroom norms, then calculates the gap between required and available (usable) classrooms.

### UDISE+ Classroom Norms

| school_category           | Students per Classroom | Rationale                            |
| ------------------------- | ---------------------- | ------------------------------------ |
| 1 (Primary I–V)           | 30                     | RTE Act 2009 norm for primary        |
| 2 (Primary + UP I–VIII)   | 30                     | RTE composite primary norm           |
| 3 (All I–XII)             | 30                     | Primary-anchored composite           |
| 4 (Upper Primary VI–VIII) | 35                     | RMSA norm for upper primary          |
| 5 (UP + Sec + HS VI–XII)  | 35                     | RMSA composite                       |
| 6 (I–X)                   | 40                     | Secondary-weighted composite         |
| 7 (VI–X)                  | 40                     | Secondary norm                       |
| 8 (Secondary IX–X)        | 40                     | RMSA secondary norm                  |
| 9 (Sec + HS IX–XII)       | 40                     | Secondary-weighted                   |
| 10 (HS only XI–XII)       | 40                     | Higher secondary norm                |
| 11 (All I–XII)            | 40                     | Alias of category 3 with higher norm |

### Formulas

$$\text{required\_class\_rooms} = \left\lceil \frac{\text{total\_enrolment}}{\text{norm}} \right\rceil$$

$$\text{classroom\_gap} = \max(0,\; \text{required\_class\_rooms} - \text{usable\_class\_rooms})$$

### SQL Pattern

```sql
UPDATE infrastructure_details i
JOIN yearly_metrics y ON i.school_id = y.school_id AND i.academic_year = y.academic_year
JOIN schools s ON i.school_id = s.school_id
SET
    i.required_class_rooms = CEIL(y.total_enrolment / CASE
        WHEN s.school_category IN (1,2,3) THEN 30
        WHEN s.school_category IN (4,5) THEN 35
        ELSE 40
    END),
    i.classroom_gap = GREATEST(
        CEIL(y.total_enrolment / CASE ... END) - i.usable_class_rooms, 0
    )
WHERE i.academic_year = :year
```

### Execution Flow

1. Create indexes on `infrastructure_details` and `yearly_metrics`
2. For each academic year (7 iterations):
   - Execute norm-based UPDATE
   - Log rows affected
3. Verify: count non-NULL `classroom_gap` values

### Performance

- Batched by year (~63k rows per UPDATE)
- Two B-tree indexes enable efficient JOIN
- Total: ~437k rows updated across 7 passes

---

## 3.2 Phase 3 — Teacher Adequacy Engine

**File:** `engines/teacher_adequacy_engine.py`
**Type:** Norm-based computation
**Operation:** UPDATE (modifies `teacher_metrics` in-place)
**Rows Affected:** 437,106

### What It Does

Computes how many teachers each school **should** have based on Pupil-Teacher Ratio (PTR) norms, then calculates the gap between required and actual staffing.

### PTR Norms

| school_category            | Students per Teacher | Rationale                                                                  |
| -------------------------- | -------------------- | -------------------------------------------------------------------------- |
| 1, 2, 3 (Primary-anchored) | 30                   | RTE Act mandated 30:1 ratio                                                |
| 4 (Upper Primary only)     | 35                   | RMSA relaxed ratio                                                         |
| 5, 6, 7, 8, 9, 10, 11      | 30 or 35             | Category-specific (mostly 30 for primary-composite, 35 for secondary-only) |

**Exact mapping:**

| Categories         | PTR Norm |
| ------------------ | -------- |
| 1, 2, 3, 5, 6      | 30       |
| 4, 7, 8, 9, 10, 11 | 35       |

### Formulas

$$\text{required\_teachers} = \left\lceil \frac{\text{total\_enrolment}}{\text{ptr\_norm}} \right\rceil$$

$$\text{teacher\_gap} = \max(0,\; \text{required\_teachers} - \text{total\_teachers})$$

### Execution Flow

1. Create index on `teacher_metrics(school_id, academic_year)`
2. For each academic year (7 iterations):
   - Execute PTR-based UPDATE
   - Log rows affected
3. Verify: count non-NULL `teacher_gap` values

---

## 3.3 Phase 4 — Compliance Risk Engine

**File:** `engines/compliance_risk_engine.py`
**Type:** Composite weighted scoring (norm-based + statistical)
**Operation:** UPDATE (adds 5 columns to `infrastructure_details`)
**Rows Affected:** 437,106
**Prerequisite:** Phase 2 AND Phase 3 must complete first

### What It Does

Computes a composite risk score for every school-year record by combining teacher deficit severity, classroom deficit severity, and enrolment growth instability. Classifies each school into one of four risk levels.

### Three-Pass Execution

**Pass 1 — Deficit Ratios (per year batch):**

$$\text{teacher\_deficit\_ratio} = \min\!\Big(1.0,\; \frac{\text{teacher\_gap}}{\max(\text{required\_teachers}, 1)}\Big)$$

$$\text{classroom\_deficit\_ratio} = \min\!\Big(1.0,\; \frac{\text{classroom\_gap}}{\max(\text{required\_class\_rooms}, 1)}\Big)$$

Ratios are capped at 1.0 to prevent extreme outliers from dominating.

**Pass 2 — Enrolment Growth Rate (all years at once):**

$$\text{growth\_rate} = \frac{E_t - E_{t-1}}{E_{t-1}}$$

Computed via `LAG(total_enrolment, 1) OVER (PARTITION BY school_id ORDER BY academic_year)`. First year for each school gets NULL growth (no prior data).

**Pass 3 — Composite Risk Score (per year batch):**

$$\text{risk\_score} = 0.45 \times \text{teacher\_deficit\_ratio} + 0.35 \times \text{classroom\_deficit\_ratio} + 0.20 \times |\text{growth\_rate}|$$

### Weight Rationale

| Component                   | Weight | Justification                                                                       |
| --------------------------- | ------ | ----------------------------------------------------------------------------------- |
| Teacher deficit             | 0.45   | Teachers are the most critical resource — no substitute for instruction             |
| Classroom deficit           | 0.35   | Physical infrastructure is the second binding constraint                            |
| Enrolment growth (absolute) | 0.20   | Rapid change (either growth OR decline) signals instability and planning difficulty |

### Risk Level Thresholds

| Level      | Condition                | Colour Code | Count   |
| ---------- | ------------------------ | ----------- | ------- |
| `CRITICAL` | risk_score ≥ 0.60        | Red         | 4,153   |
| `HIGH`     | 0.40 ≤ risk_score < 0.60 | Orange      | 79,226  |
| `MODERATE` | 0.20 ≤ risk_score < 0.40 | Yellow      | 188,553 |
| `LOW`      | risk_score < 0.20        | Green       | 165,174 |

### Downstream Impact

The 5 columns added here (`teacher_deficit_ratio`, `classroom_deficit_ratio`, `enrolment_growth_rate`, `risk_score`, `risk_level`) are consumed by:

- Phase 5 (Prioritisation) — ranks by `risk_score`
- Phase 7 (Risk Trend) — tracks `risk_score` over time
- Phase 8 (District Compliance) — aggregates `risk_score` and `risk_level` counts

---

## 3.4 Phase 5 — Prioritisation Engine

**File:** `engines/prioritisation_engine.py`
**Type:** Statistical ranking (window functions)
**Operation:** INSERT into new table `school_priority_index`
**Rows Created:** 437,106
**Prerequisite:** Phase 4

### What It Does

Ranks all schools within each academic year by their composite risk score using SQL window functions. Assigns priority buckets and identifies persistently high-risk schools.

### Core SQL Pattern

```sql
INSERT INTO school_priority_index (school_id, academic_year, risk_score, risk_rank, percentile, priority_bucket, persistent_high_risk)
SELECT
    i.school_id,
    i.academic_year,
    i.risk_score,
    RANK() OVER (PARTITION BY i.academic_year ORDER BY i.risk_score DESC)                AS risk_rank,
    PERCENT_RANK() OVER (PARTITION BY i.academic_year ORDER BY i.risk_score DESC)        AS percentile,
    CASE
        WHEN PERCENT_RANK() OVER (...) < 0.05 THEN 'TOP_5'
        WHEN PERCENT_RANK() OVER (...) < 0.10 THEN 'TOP_10'
        WHEN PERCENT_RANK() OVER (...) < 0.20 THEN 'TOP_20'
        ELSE 'STANDARD'
    END AS priority_bucket,
    CASE
        WHEN LAG(i.risk_level, 1) OVER (PARTITION BY i.school_id ORDER BY i.academic_year)
             IN ('CRITICAL','HIGH')
         AND LAG(i.risk_level, 2) OVER (PARTITION BY i.school_id ORDER BY i.academic_year)
             IN ('CRITICAL','HIGH')
        THEN 1 ELSE 0
    END AS persistent_high_risk
FROM infrastructure_details i
WHERE i.academic_year = :year
```

### Output Distribution

| Bucket                   | Count      | Percentage |
| ------------------------ | ---------- | ---------- |
| TOP_5                    | 22,195     | 5.1%       |
| TOP_10                   | 21,699     | 5.0%       |
| TOP_20                   | 44,029     | 10.1%      |
| STANDARD                 | 349,183    | 79.9%      |
| **Persistent high-risk** | **10,588** | **2.4%**   |

---

## 3.5 Phase 6 — Budget Allocation Engine

**File:** `engines/budget_allocation_engine.py`
**Type:** Simulation (constrained optimisation)
**Operation:** INSERT into new table `budget_simulation`
**Rows Created:** 437,106
**Prerequisite:** Phase 5

### What It Does

Simulates how a fixed annual budget would be distributed across schools if allocation followed a strict "worst-first" (risk_rank) ordering. Schools are served in priority order until the classroom construction budget (₹50Cr → 7,000 classrooms) and teacher posting limit (10,000) are exhausted.

### Allocation Logic

```
FOR each academic_year:
    1. JOIN school_priority_index + infrastructure_details + teacher_metrics
    2. ORDER BY risk_rank ASC (highest priority first)
    3. Assign ROW_NUMBER as allocation_order
    4. Compute:
       cumulative_classrooms = SUM(classroom_gap) OVER (ORDER BY alloc_order)
       cumulative_teachers   = SUM(teacher_gap)   OVER (ORDER BY alloc_order)
    5. IF cumulative_classrooms ≤ 7,000:
         classrooms_allocated = classroom_gap
       ELSE:
         classrooms_allocated = 0
    6. IF cumulative_teachers ≤ 10,000:
         teachers_allocated = teacher_gap
       ELSE:
         teachers_allocated = 0
    7. estimated_cost = classrooms_allocated × 500,000
    8. cumulative_cost = SUM(estimated_cost) OVER (ORDER BY alloc_order)
    9. allocation_status:
         FUNDED           if classrooms_allocated > 0 OR teachers_allocated > 0
         PARTIALLY_FUNDED if only one type allocated
         UNFUNDED         if nothing allocated
```

### Design Decisions

- **Why worst-first?** Ensures the most critical schools receive resources before budget exhaustion. This is the standard government approach under SSA/Samagra Shiksha.
- **Why fixed budget?** Reflects real-world annual budgetary ceilings from state finance departments.
- **Why separate classroom/teacher limits?** Classroom construction comes from capital expenditure; teacher recruitment comes from a separate establishment budget.

---

## 3.6 Phase 7 — Risk Trend Engine

**File:** `engines/risk_trend_engine.py`
**Type:** Statistical (longitudinal analysis)
**Operation:** INSERT into new table `risk_trend`
**Rows Created:** 437,106
**Prerequisite:** Phase 4

### What It Does

Analyses how each school's risk score has changed year-over-year across the full 7-year window. Classifies each school-year as improving, stable, or deteriorating. Flags chronic schools (stuck at high risk for 3+ years) and volatile schools (large annual swings).

### Core Query Pattern

```sql
INSERT INTO risk_trend (school_id, academic_year, risk_score, prev_risk_score,
                        risk_delta, trend_direction, is_chronic, is_volatile)
SELECT
    i.school_id,
    i.academic_year,
    i.risk_score,
    LAG(i.risk_score, 1) OVER w                                    AS prev_risk_score,
    i.risk_score - LAG(i.risk_score, 1) OVER w                    AS risk_delta,
    CASE
        WHEN LAG(i.risk_score, 1) OVER w IS NULL  THEN 'BASELINE'
        WHEN (i.risk_score - LAG(...)) < -0.05    THEN 'IMPROVING'
        WHEN (i.risk_score - LAG(...)) > 0.05     THEN 'DETERIORATING'
        ELSE 'STABLE'
    END,
    CASE WHEN <3-year high-risk check> THEN 1 ELSE 0 END,
    CASE WHEN ABS(risk_delta) > 0.15 THEN 1 ELSE 0 END
FROM infrastructure_details i
WINDOW w AS (PARTITION BY i.school_id ORDER BY i.academic_year)
```

### Output Distribution

| Category      | Count       | Meaning                                |
| ------------- | ----------- | -------------------------------------- |
| BASELINE      | 67,343      | First year — no prior year to compare  |
| IMPROVING     | 123,487     | Risk dropped by > 0.05 vs prior year   |
| STABLE        | 170,401     | Risk changed by ≤ ±0.05                |
| DETERIORATING | 75,875      | Risk increased by > 0.05               |
| **Chronic**   | **10,588**  | HIGH/CRITICAL for 3+ consecutive years |
| **Volatile**  | **160,357** | ABS(risk_delta) > 0.15 in any year     |

---

## 3.7 Phase 8 — District Compliance Index Engine

**File:** `engines/district_compliance_engine.py`
**Type:** Aggregation + Rule-based grading
**Operation:** INSERT into new table `district_compliance_index`
**Rows Created:** 182 (26 districts × 7 years)
**Prerequisite:** Phase 4

### What It Does

Rolls school-level risk data up to the district level. Computes aggregate statistics (average risk, percentage in each risk tier), assigns compliance grades, tracks year-over-year progress, and ranks districts against each other within the state.

### Three-Step SQL Execution

**Step 1 — Populate base aggregates:**

```sql
INSERT INTO district_compliance_index
    (district, academic_year, total_schools, avg_risk_score,
     pct_critical, pct_high, pct_moderate, pct_low, compliance_grade)
SELECT
    s.district,
    i.academic_year,
    COUNT(DISTINCT i.school_id),
    AVG(i.risk_score),
    SUM(CASE WHEN risk_level='CRITICAL' THEN 1 ELSE 0 END)*100.0/COUNT(*),
    SUM(CASE WHEN risk_level='HIGH'     THEN 1 ELSE 0 END)*100.0/COUNT(*),
    SUM(CASE WHEN risk_level='MODERATE' THEN 1 ELSE 0 END)*100.0/COUNT(*),
    SUM(CASE WHEN risk_level='LOW'      THEN 1 ELSE 0 END)*100.0/COUNT(*),
    CASE
        WHEN AVG(risk_score) < 0.15 THEN 'A'
        WHEN AVG(risk_score) < 0.30 THEN 'B'
        WHEN AVG(risk_score) < 0.50 THEN 'C'
        WHEN AVG(risk_score) < 0.70 THEN 'D'
        ELSE 'F'
    END
FROM infrastructure_details i
JOIN schools s ON i.school_id = s.school_id
GROUP BY s.district, i.academic_year
```

**Step 2 — Compute YoY change:**

```sql
UPDATE district_compliance_index d1
JOIN district_compliance_index d2
  ON d1.district = d2.district
  AND d2.academic_year = <previous year of d1.academic_year>
SET d1.yoy_risk_change = d1.avg_risk_score - d2.avg_risk_score
```

**Step 3 — Compute state rank:**

```sql
UPDATE district_compliance_index d
JOIN (
    SELECT id,
           RANK() OVER (PARTITION BY academic_year ORDER BY avg_risk_score ASC) AS rnk
    FROM district_compliance_index
) sub ON d.id = sub.id
SET d.state_rank = sub.rnk
```

### Key Insight

All 26 AP districts fall in grades B (96 records) and C (86 records). No district reaches grade A (< 0.15 avg risk) or drops to D/F (> 0.50). This indicates a structurally moderate level of under-resourcing across the state, with no extreme outliers.

---

## 3.8 Phase 9 — Proposal Validation Engine

**File:** `engines/proposal_validation_engine.py`
**Type:** Simulation + Rule-based validation
**Operation:** INSERT into two new tables
**Rows Created:** 437,106 proposals + 437,106 validations
**Prerequisite:** Phase 2 AND Phase 3

### What It Does

1. **Generates synthetic proposals** — Simulates what schools would request using CRC32-based deterministic noise (factor 0.70–1.49) applied to actual gaps
2. **Validates proposals** — Compares requested quantities against actual gaps using ratio-based rules to detect over-requesting, under-requesting, and claims without actual deficits

### Validation Decision Tree

```
IF (classroom_gap = 0 AND teacher_gap = 0) AND (requested_cr > 0 OR requested_tr > 0):
    → REJECTED, reason: NO_DEFICIT

ELSE IF classroom_ratio > 1.50:
    → REJECTED, reason: CLASSROOM_OVER_REQUEST

ELSE IF teacher_ratio > 1.50:
    → REJECTED, reason: TEACHER_OVER_REQUEST

ELSE IF classroom_ratio BETWEEN 1.20 AND 1.50:
    → FLAGGED, reason: CLASSROOM_MODERATE_OVER

ELSE IF teacher_ratio BETWEEN 1.20 AND 1.50:
    → FLAGGED, reason: TEACHER_MODERATE_OVER

ELSE IF classroom_ratio < 0.50 AND classroom_gap > 0:
    → FLAGGED, reason: CLASSROOM_UNDER_REQUEST

ELSE IF teacher_ratio < 0.50 AND teacher_gap > 0:
    → FLAGGED, reason: TEACHER_UNDER_REQUEST

ELSE IF (requested_cr = 0 AND requested_tr = 0) AND (gaps = 0):
    → ACCEPTED, reason: NO_REQUEST

ELSE:
    → ACCEPTED, reason: WITHIN_TOLERANCE
```

### Why CRC32 for Noise?

- **Deterministic:** Same school_id + year + salt always produces the same noise → reproducible results
- **Uniform distribution:** CRC32 MOD 80 gives values 0–79 → factors 0.70–1.49
- **No randomness:** Unlike `RAND()`, CRC32 doesn't change between runs, making the simulation verifiable

---

## 3.9 Phase 10 — Forecasting Engine

**File:** `engines/forecasting_engine.py`
**Type:** Statistical forecasting (extrapolation)
**Operation:** INSERT into new table `enrolment_forecast`
**Rows Created:** 183,951 (61,317 schools × 3 horizons)
**Prerequisite:** Phase 2 AND Phase 3

### What It Does

Projects future enrolment for each school at T+1, T+2, and T+3 years ahead, using a weighted 3-year moving average of historical growth. Then applies UDISE+ norms to compute future classroom and teacher requirements and gaps.

### Growth Computation — Why Weighted Moving Average?

| Approach                | Pros                                      | Cons                                           | Decision                   |
| ----------------------- | ----------------------------------------- | ---------------------------------------------- | -------------------------- |
| Simple YoY              | Easy                                      | Noisy, single-year anomalies dominate          | Rejected                   |
| Linear regression       | Robust                                    | Requires scipy, complex for 437k rows in SQL   | Rejected                   |
| **Weighted moving avg** | **Recent trends weighted more; pure SQL** | **Slightly less accurate than regression**     | **Selected**               |
| ARIMA/ML                | Most accurate                             | Requires per-school model training; 67k models | **Implemented (Phase 11)** |

### Growth Rate Formula (Weighted 3-Year)

$$g = \frac{3(E_t - E_{t-1}) + 2(E_{t-1} - E_{t-2}) + 1(E_{t-2} - E_{t-3})}{6 \cdot E_{t-1}}$$

- Weight 3 on the most recent change → recent trends matter most
- Weight 1 on the oldest change → historical momentum still considered
- Division by $6 \cdot E_{t-1}$ normalises to a rate

### Key Technical Decision — LAG Window Scoping

**Problem encountered during development:** When LAG() was placed inside a `WHERE academic_year = :latest` filter, each school only had 1 row visible, so LAG() returned NULL for all schools → growth = 0.0 everywhere.

**Solution:** Compute LAG across ALL years in an inner subquery (full partition window), THEN filter to the latest year in an outer query:

```sql
SELECT * FROM (
    SELECT *,
           LAG(total_enrolment, 1) OVER (PARTITION BY school_id ORDER BY academic_year) AS lag1,
           LAG(total_enrolment, 2) OVER (...) AS lag2,
           LAG(total_enrolment, 3) OVER (...) AS lag3
    FROM yearly_metrics
) sub
WHERE sub.academic_year = :latest_year
```

### Projection Example

For a school with:

- Base enrolment = 500, growth rate = -0.05 (declining 5%/year)
- School category 1, classroom norm = 30, PTR norm = 30
- Current classrooms = 10, current teachers = 12

| Horizon | Projected Enrolment | Classrooms Req | Teachers Req | Classroom Gap | Teacher Gap |
| ------- | ------------------- | -------------- | ------------ | ------------- | ----------- |
| T+1     | 475                 | 16             | 16           | 6             | 4           |
| T+2     | 451                 | 16             | 16           | 6             | 4           |
| T+3     | 429                 | 15             | 15           | 5             | 3           |

---

# 4. Component Classification Matrix

Every computation in the system falls into one of six categories. This classification clarifies what is objective (norm-based), what involves modelling choices (statistical), and what simulates real-world processes (simulation).

| Category        | Definition                                                                                   | Examples in System                                                                                                                               |
| --------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Norm-based**  | Applies government-mandated standards (RTE Act, RMSA, SSA) with no analytical discretion     | Classroom norms (30/35/40), PTR norms (30/35), classroom_gap, teacher_gap, required_class_rooms, required_teachers                               |
| **Rule-based**  | Applies expert-defined thresholds with clear if/then logic                                   | Risk level (CRITICAL/HIGH/MODERATE/LOW), compliance grade (A–F), proposal decision (ACCEPTED/FLAGGED/REJECTED), trend direction, priority bucket |
| **Statistical** | Uses mathematical formulas, window functions, or aggregations to derive quantities from data | risk_score (weighted composite), deficit ratios, RANK(), PERCENT_RANK(), LAG(), growth rate, confidence score, weighted moving average           |
| **Simulation**  | Models hypothetical scenarios that don't reflect actual data                                 | Budget allocation (constrained optimisation), synthetic demand proposals (CRC32 noise)                                                           |
| **Forecasting** | Projects future values based on historical patterns                                          | Enrolment forecast (T+1/T+2/T+3), projected classroom gap, projected teacher gap                                                                 |
| **AI / ML**     | Learns patterns from data without explicit programming                                       | **Not yet implemented.** Planned for: anomaly detection in proposals, demand prediction via neural networks, NLP-based report generation         |

### Per-Column Classification

| Table                       | Column                              | Category                          |
| --------------------------- | ----------------------------------- | --------------------------------- |
| `infrastructure_details`    | `required_class_rooms`              | Norm-based                        |
| `infrastructure_details`    | `classroom_gap`                     | Norm-based (derived)              |
| `infrastructure_details`    | `teacher_deficit_ratio`             | Statistical                       |
| `infrastructure_details`    | `classroom_deficit_ratio`           | Statistical                       |
| `infrastructure_details`    | `enrolment_growth_rate`             | Statistical                       |
| `infrastructure_details`    | `risk_score`                        | Statistical (weighted composite)  |
| `infrastructure_details`    | `risk_level`                        | Rule-based                        |
| `teacher_metrics`           | `required_teachers`                 | Norm-based                        |
| `teacher_metrics`           | `teacher_gap`                       | Norm-based (derived)              |
| `school_priority_index`     | `risk_rank`                         | Statistical (RANK window)         |
| `school_priority_index`     | `percentile`                        | Statistical (PERCENT_RANK window) |
| `school_priority_index`     | `priority_bucket`                   | Rule-based                        |
| `school_priority_index`     | `persistent_high_risk`              | Statistical (longitudinal LAG)    |
| `budget_simulation`         | `classrooms_allocated`              | Simulation                        |
| `budget_simulation`         | `teachers_allocated`                | Simulation                        |
| `budget_simulation`         | `estimated_cost`                    | Simulation                        |
| `budget_simulation`         | `allocation_status`                 | Simulation + Rule-based           |
| `risk_trend`                | `prev_risk_score`                   | Statistical (LAG)                 |
| `risk_trend`                | `risk_delta`                        | Statistical (difference)          |
| `risk_trend`                | `trend_direction`                   | Rule-based                        |
| `risk_trend`                | `is_chronic`                        | Statistical (longitudinal)        |
| `risk_trend`                | `is_volatile`                       | Rule-based (threshold)            |
| `district_compliance_index` | `avg_risk_score`                    | Aggregated                        |
| `district_compliance_index` | `pct_critical` / `pct_high` / etc.  | Aggregated                        |
| `district_compliance_index` | `compliance_grade`                  | Rule-based                        |
| `district_compliance_index` | `yoy_risk_change`                   | Statistical (YoY)                 |
| `district_compliance_index` | `state_rank`                        | Statistical (RANK window)         |
| `school_demand_proposals`   | `classrooms_requested`              | Simulation (CRC32 noise)          |
| `school_demand_proposals`   | `teachers_requested`                | Simulation (CRC32 noise)          |
| `proposal_validations`      | `classroom_ratio` / `teacher_ratio` | Statistical (ratio)               |
| `proposal_validations`      | `decision_status`                   | Rule-based                        |
| `proposal_validations`      | `reason_code`                       | Rule-based                        |
| `proposal_validations`      | `confidence_score`                  | Statistical                       |
| `enrolment_forecast`        | `avg_growth_rate`                   | Statistical (weighted moving avg) |
| `enrolment_forecast`        | `projected_enrolment`               | Forecasting                       |
| `enrolment_forecast`        | `projected_classrooms_req`          | Forecasting + Norm-based          |
| `enrolment_forecast`        | `projected_teachers_req`            | Forecasting + Norm-based          |
| `enrolment_forecast`        | `projected_classroom_gap`           | Forecasting                       |
| `enrolment_forecast`        | `projected_teacher_gap`             | Forecasting                       |

---

# 5. Dashboard Design — Multi-Level Governance

The system supports four hierarchical dashboard levels, each serving a distinct governance persona with different decision-making authority.

## 5.1 State-Level Dashboard (Commissioner / Secretary of Education)

**User:** State Commissioner of School Education, Secretary (Education)
**Decision Authority:** Statewide policy, budget allocation, district performance review

### Panel 1 — State Risk Overview Map

| Visualisation                                                            | Source Table                                  | Query                                                                            |
| ------------------------------------------------------------------------ | --------------------------------------------- | -------------------------------------------------------------------------------- |
| Choropleth map (26 districts, coloured by compliance_grade)              | `district_compliance_index`                   | `SELECT district, compliance_grade, avg_risk_score WHERE academic_year = latest` |
| KPI cards: Total CRITICAL schools, Total FUNDED schools, Budget utilised | `infrastructure_details`, `budget_simulation` | Aggregate counts with filters                                                    |

### Panel 2 — Trend Sparklines

| Visualisation                                     | Source Table                | Query                                                              |
| ------------------------------------------------- | --------------------------- | ------------------------------------------------------------------ |
| Line chart: state-average risk score over 7 years | `district_compliance_index` | `SELECT academic_year, AVG(avg_risk_score) GROUP BY academic_year` |
| Stacked bar: schools by risk_level per year       | `infrastructure_details`    | `SELECT academic_year, risk_level, COUNT(*) GROUP BY 1, 2`         |

### Panel 3 — Budget Simulation Summary

| Visualisation                                     | Source Table                       | Query                                                                                |
| ------------------------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------ |
| Donut chart: FUNDED / PARTIALLY_FUNDED / UNFUNDED | `budget_simulation`                | `SELECT allocation_status, COUNT(*) WHERE academic_year = latest GROUP BY 1`         |
| Table: Top 10 districts by unfunded gap           | `budget_simulation` JOIN `schools` | `SUM(classroom_gap - classrooms_allocated) GROUP BY district ORDER BY DESC LIMIT 10` |

### Panel 4 — Forecasting Alert

| Visualisation                                                   | Source Table                        | Query                                                                              |
| --------------------------------------------------------------- | ----------------------------------- | ---------------------------------------------------------------------------------- |
| Bar chart: projected classroom gap at T+1, T+2, T+3 (statewide) | `enrolment_forecast`                | `SELECT years_ahead, SUM(projected_classroom_gap) GROUP BY years_ahead`            |
| Table: Top 10 districts by T+3 projected gap                    | `enrolment_forecast` JOIN `schools` | `SUM(projected_classroom_gap) WHERE years_ahead=3 GROUP BY district ORDER BY DESC` |

---

## 5.2 District-Level Dashboard (District Education Officer — DEO)

**User:** District Education Officer, District Collector
**Decision Authority:** District budget allocation, block-level review, school inspections

### Panel 1 — District Compliance Card

| Visualisation                                  | Source Table                | Query                                                                                                 |
| ---------------------------------------------- | --------------------------- | ----------------------------------------------------------------------------------------------------- |
| Large grade badge (A/B/C/D/F) with trend arrow | `district_compliance_index` | `SELECT compliance_grade, yoy_risk_change, state_rank WHERE district = :d AND academic_year = latest` |
| Gauge: avg_risk_score (0–1 scale)              | `district_compliance_index` | Same query                                                                                            |

### Panel 2 — Block-wise Heatmap

| Visualisation                               | Source Table                            | Query                                                                                             |
| ------------------------------------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Heatmap: blocks × risk levels               | `infrastructure_details` JOIN `schools` | `SELECT block, risk_level, COUNT(*) WHERE district = :d AND academic_year = latest GROUP BY 1, 2` |
| Highlight: blocks with highest pct_critical | Same                                    | Derived from heatmap data                                                                         |

### Panel 3 — Priority Schools List

| Visualisation                                        | Source Table                           | Query                                                                                                                  |
| ---------------------------------------------------- | -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Sortable table: TOP_5 and TOP_10 schools in district | `school_priority_index` JOIN `schools` | `SELECT * WHERE district = :d AND priority_bucket IN ('TOP_5','TOP_10') AND academic_year = latest ORDER BY risk_rank` |
| Badge: persistent_high_risk flag                     | Same                                   | Filter `persistent_high_risk = 1`                                                                                      |

### Panel 4 — Proposal Validation Summary

| Visualisation                                      | Source Table                          | Query                                                                                        |
| -------------------------------------------------- | ------------------------------------- | -------------------------------------------------------------------------------------------- |
| Pie chart: ACCEPTED / FLAGGED / REJECTED proposals | `proposal_validations` JOIN `schools` | `SELECT decision_status, COUNT(*) WHERE district = :d AND academic_year = latest GROUP BY 1` |
| Table: FLAGGED proposals with reason_code          | Same                                  | `WHERE decision_status = 'FLAGGED' ORDER BY confidence_score ASC`                            |

### Panel 5 — District Trend Line

| Visualisation                                    | Source Table                | Query                                                                             |
| ------------------------------------------------ | --------------------------- | --------------------------------------------------------------------------------- |
| Line chart: district avg_risk_score over 7 years | `district_compliance_index` | `SELECT academic_year, avg_risk_score WHERE district = :d ORDER BY academic_year` |
| Sparkline: yoy_risk_change trajectory            | Same                        | Derived                                                                           |

---

## 5.3 Block-Level Dashboard (Block Education Officer — BEO / MEO)

**User:** Block Education Officer, Mandal Education Officer
**Decision Authority:** School visits, local resource deployment, proposal endorsement

### Panel 1 — Block Summary

| Visualisation                                          | Source Table                                             | Query                                                     |
| ------------------------------------------------------ | -------------------------------------------------------- | --------------------------------------------------------- |
| KPI cards: Total schools, Critical count, Funded count | `infrastructure_details`, `budget_simulation`, `schools` | Aggregate filtered by `block = :b AND district = :d`      |
| Mini bar: risk_level distribution                      | `infrastructure_details`                                 | `SELECT risk_level, COUNT(*) WHERE block = :b GROUP BY 1` |

### Panel 2 — School List with Risk Indicators

| Visualisation                                                                                  | Source Table            | Query                      |
| ---------------------------------------------------------------------------------------------- | ----------------------- | -------------------------- |
| Scrollable table: all schools in block, risk_score, risk_level, trend_direction, budget status | Multiple tables joined  | Full outer view per school |
| Colour-coded rows: red = CRITICAL, orange = HIGH                                               | Derived from risk_level | —                          |

### Panel 3 — Chronic & Volatile Schools

| Visualisation                               | Source Table                | Query                                                            |
| ------------------------------------------- | --------------------------- | ---------------------------------------------------------------- |
| Filtered list: `is_chronic = TRUE` schools  | `risk_trend` JOIN `schools` | `WHERE block = :b AND is_chronic = 1 AND academic_year = latest` |
| Filtered list: `is_volatile = TRUE` schools | Same                        | `WHERE is_volatile = 1`                                          |

---

## 5.4 School-Level Dashboard (Headmaster / Principal)

**User:** School Headmaster, Principal, SDMC (School Development & Monitoring Committee)
**Decision Authority:** Proposal submission, internal resource management, facility maintenance

### Panel 1 — School Risk Card

| Visualisation                                   | Source Table             | Query                                             |
| ----------------------------------------------- | ------------------------ | ------------------------------------------------- |
| Risk score gauge (0–1) with risk_level badge    | `infrastructure_details` | `WHERE school_id = :s AND academic_year = latest` |
| Trend arrow: IMPROVING / STABLE / DETERIORATING | `risk_trend`             | `WHERE school_id = :s AND academic_year = latest` |
| Persistent high-risk warning badge              | `school_priority_index`  | `persistent_high_risk = 1`                        |

### Panel 2 — Gap Analysis

| Visualisation                                             | Source Table             | Query                                         |
| --------------------------------------------------------- | ------------------------ | --------------------------------------------- |
| Side-by-side bars: classrooms (actual vs required vs gap) | `infrastructure_details` | Single row for school-year                    |
| Side-by-side bars: teachers (actual vs required vs gap)   | `teacher_metrics`        | Single row for school-year                    |
| Historical line: enrolment over 7 years                   | `yearly_metrics`         | `WHERE school_id = :s ORDER BY academic_year` |

### Panel 3 — Proposal Status

| Visualisation                                                | Source Table              | Query                                             |
| ------------------------------------------------------------ | ------------------------- | ------------------------------------------------- |
| Card: classrooms_requested, teachers_requested               | `school_demand_proposals` | `WHERE school_id = :s AND academic_year = latest` |
| Badge: decision_status (ACCEPTED / FLAGGED) with reason_code | `proposal_validations`    | Same filter                                       |
| Confidence meter: confidence_score (0–1)                     | Same                      | Same                                              |

### Panel 4 — Forecast

| Visualisation                                           | Source Table         | Query                                                   |
| ------------------------------------------------------- | -------------------- | ------------------------------------------------------- |
| Line chart: projected enrolment at T+1, T+2, T+3        | `enrolment_forecast` | `WHERE school_id = :s`                                  |
| Table: projected classroom gap, teacher gap per horizon | Same                 | All 3 rows                                              |
| Alert: if T+3 gap > current gap, show growth warning    | Computed             | `projected_classroom_gap[T+3] > classroom_gap[current]` |

### Panel 5 — Facility Checklist

| Visualisation             | Source Table             | Query                                                                                                  |
| ------------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------ |
| Checklist with ✓/✗ icons  | `infrastructure_details` | Boolean columns: drinking_water, electricity, internet, girls_toilet, ramp, CWSN toilet, resource_room |
| Building condition badge  | Same                     | `building_condition`                                                                                   |
| Classroom condition score | Same                     | `classroom_condition_score`                                                                            |

---

# 6. Governance & Decision Workflows

## 6.1 Annual Planning Cycle

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ANNUAL WORKFLOW TIMELINE                             │
│                                                                         │
│  Q1 (Apr–Jun)          Q2 (Jul–Sep)         Q3 (Oct–Dec)    Q4 (Jan–Mar)│
│  ──────────────        ──────────────       ──────────────   ──────────  │
│                                                                         │
│  1. UDISE+ data        3. Run Risk          5. Budget        7. Monitor │
│     collection            Engine               Simulation      & Track  │
│                                                                         │
│  2. Load into          4. Generate           6. Validate      8. Year-  │
│     system                Priority              Proposals       end      │
│                           Rankings                              Report   │
│                                                                         │
│  Data Sources:         Engines:              Engines:         Engines:   │
│  load_data.py          Phase 2–5             Phase 6, 9       Phase 7–8  │
│  load_master_data.py                         Phase 10                    │
└─────────────────────────────────────────────────────────────────────────┘
```

## 6.2 Decision Flow — Resource Allocation

```
UDISE+ Data Collected (Q1)
        │
        ▼
Phase 2–3: Compute Infrastructure & Teacher Gaps
        │
        ▼
Phase 4: Compute Composite Risk Score
        │
        ▼
Phase 5: Rank Schools by Risk (statistical priority)
        │
        ▼
    ┌───────────────────────────────────────┐
    │  District Education Officer (DEO)      │
    │  Reviews TOP_5 and TOP_10 schools      │
    │  Verifies persistent high-risk flags   │
    │  Endorses priority list                │
    └───────────┬───────────────────────────┘
                │
                ▼
Phase 6: Budget Simulation (₹50Cr/year constraint)
        │
        ▼
    ┌───────────────────────────────────────┐
    │  State Commissioner                    │
    │  Reviews district-wise allocation      │
    │  Adjusts budget parameters if needed   │
    │  Approves final allocation plan        │
    └───────────┬───────────────────────────┘
                │
                ▼
Phase 9: Proposal Validation
        │
    ┌───┴───────────────────────────────────┐
    │  Automated Screening                   │
    │  ACCEPTED → Proceed to sanction        │
    │  FLAGGED  → Manual review by DEO       │
    │  REJECTED → Return to school for       │
    │             correction                  │
    └───────────┬───────────────────────────┘
                │
                ▼
Phase 10: Forecast — Feed next year's planning
```

## 6.3 Decision Flow — District Accountability

```
Phase 8: District Compliance Index computed
        │
        ▼
    ┌───────────────────────────────────────┐
    │  State-Level Review Meeting            │
    │                                        │
    │  For each district:                    │
    │  • Compliance Grade (A/B/C/D/F)        │
    │  • YoY Risk Change (↑/↓/→)            │
    │  • State Rank (1–26)                   │
    │                                        │
    │  Actions:                              │
    │  • Grade C/D/F → Improvement plan      │
    │  • Negative YoY → Root cause analysis  │
    │  • Rank drop → Additional monitoring   │
    └───────────────────────────────────────┘
```

---

# 7. Product Vision

## 7.1 Problem Statement

The Government of Andhra Pradesh manages approximately 67,000 schools across 26 districts. Each year, administrators must decide:

1. **Which schools need more classrooms?** (Infrastructure gap)
2. **Which schools need more teachers?** (Teacher adequacy gap)
3. **Which schools are most at risk?** (Compliance risk)
4. **In what order should limited resources be allocated?** (Prioritisation)
5. **How should a fixed annual budget be distributed?** (Budget simulation)
6. **Are school resource requests legitimate?** (Proposal validation)
7. **What will the gaps look like in 3 years if no action is taken?** (Forecasting)

Currently, these decisions are made through manual spreadsheet analysis, subjective officer assessments, and political negotiation. There is no systematic, data-driven framework that integrates all dimensions of school resource planning.

## 7.2 What This System Provides

### For the State Commissioner

- A single compliance grade for each of 26 districts, updated annually
- State-wide risk heatmap showing where CRITICAL schools are concentrated
- Budget simulation showing exactly how many schools can be funded under current budget ceilings
- 3-year forecast showing whether the gap will grow or shrink without intervention
- Automated proposal screening reducing manual review workload by ~75% (only FLAGGED proposals need human review)

### For the District Education Officer

- A ranked list of the worst 5%, 10%, and 20% of schools in the district
- Persistent high-risk flags identifying schools that have been failing for 3+ years
- Block-wise heatmap revealing geographic concentration of risk
- Proposal validation results showing which school requests are suspicious
- Year-over-year trend showing whether the district is improving or deteriorating

### For the Block Education Officer

- A complete school-by-school risk assessment for their jurisdiction
- Chronic and volatile school lists for targeted intervention visits
- Budget allocation results showing which schools in their block received funding
- Forecast data to anticipate future resource needs

### For the School Headmaster

- A clear, objective risk score explaining why the school is classified as it is
- Gap analysis showing exactly how many classrooms and teachers are needed vs. available
- Proposal status showing whether their resource request was accepted, flagged, or needs correction
- Enrolment forecast to plan for future growth or manage decline

## 7.3 Design Principles

| Principle                   | Implementation                                                                                                       |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **Transparency**            | Every score, grade, and decision has a traceable formula. No black boxes.                                            |
| **Reproducibility**         | All engines are idempotent — DELETE + re-INSERT. Running any engine twice produces identical results.                |
| **Norm-grounded**           | Gap computations use official UDISE+ / RTE Act / RMSA norms, not arbitrary thresholds.                               |
| **Separation of concerns**  | Each engine reads from upstream tables and writes to its own output. No circular dependencies.                       |
| **Year-batched processing** | All mutations process one academic year at a time (~63k rows) to respect cloud database connection limits.           |
| **Governance-ready**        | The system produces outputs at State / District / Block / School levels, mapping to actual administrative hierarchy. |

## 7.4 Current Limitations & Future Roadmap

| Limitation                        | Status                            | Future Enhancement                                       |
| --------------------------------- | --------------------------------- | -------------------------------------------------------- |
| No real proposal data             | Simulated via CRC32               | Integrate actual school submission portal                |
| No teacher subject-specialisation | Only total headcount              | Add subject-wise adequacy (Math/Science/English)         |
| No geospatial optimisation        | Only tabular analysis             | Add spatial clustering for mobile school units           |
| No learning outcome data          | Risk = inputs only                | Integrate NAS (National Achievement Survey) scores       |
| ~~No ML/AI models~~               | ~~Rule-based + statistical only~~ | ✅ Phase 11: GBR-based ML forecasting engine implemented |
| Fixed budget parameters           | Hardcoded ₹50Cr / ₹5L             | Make budget parameters configurable per simulation run   |
| No attendance data                | Column exists but is NULL         | Integrate SATS (Student Attendance Tracking System)      |

---

## Phase 11 — ML-Based Enrolment Forecasting

### Architecture

```
┌──────────────┐     20 features      ┌───────────────────────────┐
│ yearly_metrics│────────────────────►│  GradientBoostingRegressor │
│ infra_details │  temporal panel      │  loss=huber, depth=4       │
│ teacher_met.  │  302k train samples  │  500 trees, lr=0.03        │
│ schools       │                      │  min_leaf=100, ss=0.8      │
└──────────────┘                      └────────────┬──────────────┘
                                                   │ growth_rate ∈ [−0.3, +0.3]
                                                   ▼
                                      ┌───────────────────────────┐
                                      │  Bias Calibration         │
                                      │  shift → training mean    │
                                      └────────────┬──────────────┘
                                                   │
                                      ┌────────────▼──────────────┐
                                      │  Compound Projection      │
                                      │  T+k = base × (1+g)^k    │
                                      │  k = 1, 2, 3              │
                                      └────────────┬──────────────┘
                                                   │
                                      ┌────────────▼──────────────┐
                                      │  ml_enrolment_forecast    │
                                      │  183,951 rows             │
                                      └───────────────────────────┘
```

### ML vs WMA Performance

| Metric            | ML (Phase 11) | WMA (Phase 10) | Winner |
| ----------------- | ------------- | -------------- | ------ |
| Enrolment R²      | 0.926         | 0.903          | **ML** |
| Enrolment MAE     | 55            | 56             | **ML** |
| Enrolment MAPE    | 38.71%        | 30.27%         | WMA    |
| T+1 classroom gap | 198,342       | 200,719        | —      |
| T+3 classroom gap | 220,546       | 247,764        | —      |

ML wins on R² and MAE; WMA wins on MAPE (small-school relative error).
Both models coexist — Phase 10 for simplicity, Phase 11 for richer insights.

### Key Design Decisions

1. **Growth rate target (not absolute)** — trees can't learn identity; predicting growth and compounding is stable
2. **Feature clipping ±0.30** — prevents out-of-distribution extrapolation from extreme growth events
3. **Compound projection** — avoids autoregressive divergence (V1/V2 showed +60-70% runaway growth)
4. **Bias calibration** — post-prediction shift corrects systematic bias from feature distribution shift
5. **Huber loss** — outlier-robust; quadratic for small errors, linear for large

### Feature Importance Insights

The top features reveal **what drives enrolment change** — actionable for policy:

- **Enrolment volatility (40%)** — unstable schools are predictably declining
- **Risk score (12%)** — Phase 4's composite risk predicts future enrolment loss
- **Classrooms (12%)** — infrastructure capacity affects student retention
- **Management type (5%)** — govt vs private has systematically different trajectories

## 7.5 Technical Architecture Summary

| Component          | Technology                                                  | Rationale                                                                          |
| ------------------ | ----------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Database           | MySQL 8.0 on Railway Cloud                                  | Managed hosting, window function support, generous free tier                       |
| ORM / Connectivity | SQLAlchemy (`create_engine`)                                | Connection pooling (`pool_recycle=280`), `pool_pre_ping=True` for cloud resilience |
| Configuration      | python-dotenv (`.env` file)                                 | `DATABASE_URL` stored securely, not in version control                             |
| Data Pipeline      | pandas                                                      | CSV reading, merging, aggregation, schema drift handling                           |
| Computation        | Raw SQL via SQLAlchemy `text()`                             | Maximum performance for 437k-row operations; avoids ORM overhead                   |
| Batch Strategy     | Year-partitioned                                            | 7 passes × ~63k rows, keeping each transaction under Railway's connection timeout  |
| Idempotency        | DELETE + re-INSERT (new tables), overwrite (UPDATE columns) | Safe to re-run any engine without data duplication                                 |

---

_Document generated from codebase analysis of 11 computation engines, 12 database tables, and 437,106 school-year records across 26 districts of Andhra Pradesh, India._
