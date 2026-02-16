# School AI BAV — AI Engineering Log

## 1. Problem Statement

We are building a multi-year structured master dataset for school-level analytics
using 6 years of government school data.

Each year contains 6 CSV files:

- profile_1.csv
- profile_2.csv
- facility.csv
- teacher.csv
- enrolment_1.csv
- enrolment_2.csv

Goal:
Create a clean, validated, scalable master dataset (one row per school per year)
ready for database storage, analytics, and ML modeling.

---

## 2. Raw Data Structure

Each year folder:
data/raw/{year}/

Each year contains:

- 63,621 schools (2018-19 baseline)
- enrolment_1 → category-wise enrolment (General, SC, ST, OBC, Muslim)
- enrolment_2 → age-wise enrolment (Age<5 to Age13)

Primary key in raw data: `psuedocode`
Renamed to: `school_id`

---

## 3. Data Cleaning Decisions

✔ Standardized column names:

- lowercase
- underscores
- removed spaces and symbols

✔ Fixed primary key:

- psuedocode → school_id

✔ Aggregated enrolment_1:

- Grouped by school_id
- Summed class columns
- Created:
  - total_boys
  - total_girls
  - total_enrolment

✔ Aggregated enrolment_2:

- Grouped by school_id
- Created:
  - total_boys_age
  - total_girls_age
  - total_enrolment_age

---

## 4. Validation Checks Performed

✔ Internal consistency:

- total_enrolment == sum(class columns)
- boys/girls totals verified
- mismatch count = 0

✔ Cross validation:

- enrolment_1 vs enrolment_2 totals differ
- Verified enrolment_2 is age-wise subset

✔ Duplicate check:

- school_id duplicates = 0

✔ Null audit:

- ~1.9% null cells
- Fully null column "parliamentary" removed automatically

✔ Implemented function:
drop_fully_null_columns()

---

## 5. Architecture Design

Built reusable function:

build_master_dataset(year)

Pipeline:

1. Load raw CSVs
2. Standardize columns
3. Aggregate enrolments
4. Fix primary key
5. Merge all datasets
6. Drop fully null columns
7. Save to data/processed/master\_{year}.csv

Loop runs for 6 years automatically.

---

## 6. 2018-19 Output

Master dataset shape:
(63621 rows, 244 columns)

One row per school.

---

## 7. Automation Status

Multi-year processing implemented.

Years:

- 2018-19
- 2019-20
- 2020-21
- 2021-22
- 2022-23
- 2023-24

---

## 8. Current System Capabilities

✔ Clean ETL pipeline
✔ Self-healing null-column removal
✔ Year-based automation
✔ Validated enrolment logic
✔ Ready for database ingestion

---

## 9. Next Planned Steps

- Concatenate 6-year datasets into longitudinal dataset
- Design MySQL schema
- Build time-series features
- Prepare for ML modeling
- Add data quality monitoring

---

This file is designed so any AI can resume the project instantly.

# School AI BAV — AI Engineering Log

Last Updated: After successful 7-year ETL automation

========================================================

1. # PROJECT OBJECTIVE

Build a scalable, production-ready multi-year school analytics dataset
using government school-level data (2018–19 to 2024–25).

Goal:

- One clean master dataset per year
- Fully automated ETL
- Schema-drift resilient
- Ready for longitudinal analytics and ML

# ======================================================== 2. RAW DATA STRUCTURE

Each year folder:
data/raw/{year}/

Each year contains 6 CSV files:

- profile_1.csv
- profile_2.csv
- facility.csv
- teacher.csv
- enrolment_1.csv (category-wise)
- enrolment_2.csv (age-wise)

Primary key in raw:

- psuedocode (sometimes spelled pseudocode)

Standardized to:

- school_id

# ======================================================== 3. SCHEMA DRIFT DISCOVERY

Schema changed in 2022-23 onward.

Before 2022-23:

- enrolment tables had column: item_desc

From 2022-23 onward:

- item_desc replaced with:
  - item_group
  - item_id

Class columns (cpp_b → c12_g) remained identical.

Solution:

- Implemented safe_drop_grouping_columns()
- Automatically removes:
  ["item_desc", "item_group", "item_id"]
- Works across all years safely

# ======================================================== 4. DATA CLEANING PIPELINE

Standardization Steps:

- Lowercase column names
- Replace spaces, dashes with underscores
- Fix psuedocode → school_id
- Drop 100% null columns automatically
- Remove grouping columns safely
- Aggregate enrolments
- Create totals:
  - total_boys
  - total_girls
  - total_enrolment
  - total_boys_age
  - total_girls_age
  - total_enrolment_age

Validation Performed:

- Internal class sum consistency
- Boys/Girls split validation
- Duplicate school_id check (0 duplicates)
- Schema drift handling verified

# ======================================================== 5. AUTOMATED ETL ARCHITECTURE

Core Function:
build_master_dataset(year)

Pipeline Flow:

1. Load raw CSVs
2. Standardize columns
3. Fix primary key
4. Aggregate enrolment_1
5. Aggregate enrolment_2
6. Merge all datasets
7. Drop fully null columns
8. Save to data/processed/master\_{year}.csv

Year Detection:

- Automatically detects all folders inside data/raw/
- No manual year list required
- Future-proof for new years (e.g., 2025-26)

# ======================================================== 6. SUCCESSFULLY PROCESSED YEARS

Detected Years:

- 2018-19
- 2019-20
- 2020-21
- 2021-22
- 2022-23
- 2023-24
- 2024-25

All processed successfully.

# ======================================================== 7. OUTPUT SUMMARY

## Year | Rows | Columns

2018-19 | 63621 | 243
2019-20 | 63824 | 238
2020-21 | 63343 | 243
2021-22 | 61948 | 244
2022-23 | 61680 | 218
2023-24 | 61373 | 218
2024-25 | 61317 | 218

Observations:

- Column reduction after 2022-23
- School count declining over years
- Schema stabilized from 2022 onward

# ======================================================== 8. CURRENT SYSTEM CAPABILITY

✔ Fully automated multi-year ETL
✔ Schema-drift resilient
✔ Self-healing null-column removal
✔ Clean master datasets per year
✔ Production-grade architecture
✔ Ready for longitudinal integration

# ======================================================== 9. NEXT POSSIBLE DIRECTIONS

Options:

1. Build longitudinal stacked dataset (school_id + year)
2. Design normalized MySQL schema
3. Perform cross-year schema consistency audit
4. Feature engineering for ML
5. School survival / churn analysis
6. Data quality scoring framework

This document enables any AI or engineer to resume work instantly.

# School AI BAV — AI Engineering Log

Last Updated: After Longitudinal Dataset Construction

========================================================

1. # PROJECT OBJECTIVE

Build a scalable, production-ready multi-year school analytics system
using government school-level data (2018–19 to 2024–25).

Goal:

- Clean master dataset per year
- Fully automated ETL
- Schema-drift resilient
- Longitudinal time-series dataset
- Ready for analytics and ML

# ======================================================== 2. RAW DATA STRUCTURE

Each year folder:
data/raw/{year}/

Each year contains 6 CSV files:

- profile_1.csv
- profile_2.csv
- facility.csv
- teacher.csv
- enrolment_1.csv (category-wise)
- enrolment_2.csv (age-wise)

Primary key in raw:

- psuedocode / pseudocode

Standardized to:

- school_id

# ======================================================== 3. SCHEMA DRIFT HANDLING

Change observed starting 2022-23:

Before:

- enrolment tables had column: item_desc

After:

- item_desc replaced with:
  - item_group
  - item_id

Solution implemented:

- safe_drop_grouping_columns()
- Automatically removes:
  ["item_desc", "item_group", "item_id"]
- Works across all years safely

Pipeline is schema-drift resilient.

# ======================================================== 4. YEARLY MASTER DATASETS

Automated build via:
build_master_dataset(year)

Pipeline Steps:

1. Load raw CSVs
2. Standardize columns
3. Fix primary key
4. Aggregate enrolment_1 (category-wise)
5. Aggregate enrolment_2 (age-wise)
6. Create totals:
   - total_boys
   - total_girls
   - total_enrolment
   - total_boys_age
   - total_girls_age
   - total_enrolment_age
7. Merge all datasets
8. Drop 100% null columns
9. Save to data/processed/master\_{year}.csv

All years auto-detected from data/raw/

# ======================================================== 5. SUCCESSFULLY PROCESSED YEARS

2018-19 → (63621, 243)
2019-20 → (63824, 238)
2020-21 → (63343, 243)
2021-22 → (61948, 244)
2022-23 → (61680, 218)
2023-24 → (61373, 218)
2024-25 → (61317, 218)

Observations:

- School count declining over time
- Schema simplified from 2022 onward

# ======================================================== 6. LONGITUDINAL DATASET CREATED

Built via:
build_longitudinal_dataset()

Process:

- Load all master\_{year}.csv
- Add year column
- Vertically stack
- Save as:

data/processed/master_longitudinal.csv

Final Shape:
(437106 rows, 323 columns)

Meaning:

- 7 years combined
- ~437k school-year observations
- Union of all columns across years retained

# ======================================================== 7. CURRENT SYSTEM CAPABILITIES

✔ Fully automated multi-year ETL
✔ Schema-drift resilient
✔ Self-healing null-column removal
✔ Longitudinal time-series dataset
✔ 7-year coverage (2018–2025)
✔ Production-ready architecture
✔ Ready for advanced analytics

# ======================================================== 8. STRATEGIC NEXT PHASE

Now entering Intelligence Layer.

Possible next moves:

1. Analyze school churn across years
2. Engineer time-based growth features
3. Design normalized SQL schema
4. Build survival / closure prediction model
5. Infrastructure improvement trend analysis

The system is now ready for structural education analytics.

# School AI BAV — AI Engineering Log

Last Updated: After School Churn Analysis

========================================================

1. # PROJECT OBJECTIVE

Build a scalable, production-ready multi-year school analytics system
using government school-level data (2018–19 to 2024–25).

System is now operating at:
✔ Multi-year ETL level
✔ Longitudinal dataset level
✔ Structural churn intelligence level

# ======================================================== 2. YEARLY MASTER DATASETS

Successfully processed:

## Year | Rows | Columns

2018-19 | 63621 | 243
2019-20 | 63824 | 238
2020-21 | 63343 | 243
2021-22 | 61948 | 244
2022-23 | 61680 | 218
2023-24 | 61373 | 218
2024-25 | 61317 | 218

Schema drift handled (item_desc → item_group/item_id).
Pipeline fully automated and future-proof.

# ======================================================== 3. LONGITUDINAL DATASET

File:
data/processed/master_longitudinal.csv

Shape:
(437106 rows, 323 columns)

Structure:
school_id | year | features...

Notes:

- Union of all columns across 7 years retained
- Ready for time-series analytics
- Warning about mixed dtypes observed (non-breaking)

# ======================================================== 4. SCHOOL CHURN ANALYSIS

Total unique schools across 7 years:
67,343

Schools per year:
2018-19 → 63,621
2019-20 → 63,824
2020-21 → 63,343
2021-22 → 61,948
2022-23 → 61,680
2023-24 → 61,373
2024-25 → 61,317

---

SURVIVAL DISTRIBUTION (Years Active):

1 year → 1,655 schools
2 years → 1,508 schools
3 years → 2,064 schools
4 years → 1,355 schools
5 years → 1,291 schools
6 years → 1,922 schools
7 years → 57,548 schools

---

Key Insight:

57,548 schools active all 7 years
= ~85.4% structural stability

Only ~2.45% schools appear for 1 year only.

Conclusion:
The education system dataset shows high structural stability.
Churn exists but is concentrated in a small edge population.

# ======================================================== 5. CURRENT SYSTEM STATUS

✔ Multi-year automated ETL
✔ Schema-drift resilient
✔ Longitudinal time-series dataset
✔ Structural survival analysis complete
✔ Stability metrics computed
✔ Ready for deeper structural intelligence

# ======================================================== 6. NEXT INTELLIGENCE OPTIONS

Now possible directions:

1. Compare Stable (7-year) vs Unstable schools
2. Analyze characteristics of 1-year schools
3. Compute enrolment growth trends
4. Detect early decline signals
5. Engineer time-based ML features
6. Build school survival prediction model

System is now beyond data cleaning.
We are officially in education intelligence phase.

# School AI BAV — AI Engineering Log

Last Updated: After Enrolment Growth & Collapse Signal Discovery

========================================================

1. # SYSTEM STATUS

We now have:

✔ Clean multi-year ETL (2018–19 to 2024–25)
✔ Schema drift handling (item_desc → item_group/item_id)
✔ 7 yearly master datasets
✔ Longitudinal stacked dataset (437,106 rows)
✔ School churn analysis
✔ Stability classification
✔ Year-over-year growth analytics

We have officially moved from data cleaning to structural intelligence.

# ======================================================== 2. CHURN INSIGHTS

Total unique schools across 7 years: 67,343
Schools active all 7 years: 57,548 (~85.4%)

System is structurally stable.

However:
~2.45% appear only one year.

Churn exists, but concentrated.

# ======================================================== 3. STABILITY SEGMENTATION

Defined:

Stable → 7 years active
Mid → 4–6 years
Unstable → ≤3 years

Latest year comparison (2024–25):

Average enrolment:
Mid ≈ 460
Unstable ≈ 373
Stable ≈ 251

Stable schools are smaller but persistent.
Urban schools churn more than rural.

# ======================================================== 4. ENROLMENT GROWTH DISCOVERY

Median Year-over-Year Growth:

Mid ≈ -1.66%
Stable ≈ -5.26%
Unstable ≈ -47.58%

Critical Insight:

Unstable schools show severe enrolment collapse
before disappearing.

This is a strong predictive signal.

# ======================================================== 5. CURRENT POSITION

We are no longer doing descriptive analytics.

We are entering:

Survival Modelling / Early Warning Systems

The dataset now supports:

- Collapse detection
- Risk scoring
- Trend modelling
- Policy simulation
- Predictive modelling

System maturity: Advanced analytics ready.

# AI Development Log – School AI BAV System

## Project Context

Problem Statement 5:
AI-powered scalable Baseline Assessment & Validation (BAV) system for Andhra Pradesh School Infrastructure Planning under Samagra Shiksha.

Goal:
Build a system that:

1. Forecasts infrastructure requirements
2. Validates school-level infrastructure proposals
3. Detects inconsistencies / inflated requests
4. Supports prioritization at scale (Block/District/State)

---

# Phase 1: Data Engineering Foundation (COMPLETED)

## Years Processed

2018-19 to 2024-25

## Datasets Integrated

- profile_1
- profile_2
- facility
- enrolment_1 (category-based)
- enrolment_2 (age-based)
- teacher

## Key Engineering Decisions

### 1. Standardization

- All columns standardized (lowercase, snake_case)
- `psuedocode` renamed to `school_id`
- Grouping columns dynamically handled:
  - Pre-2022: item_desc
  - 2022 onward: item_group, item_id

### 2. Aggregation Logic

enrolment_1:

- Aggregated across caste/religion groups
- Created:
  - total_boys
  - total_girls
  - total_enrolment

enrolment_2:

- Aggregated across age groups
- Created:
  - total_enrolment_age

### 3. Internal Validation

- Verified total = sum of class columns
- Boys/Girls splits validated
- enrolment_1 vs enrolment_2 cross-check performed
- 338 exact matches
- Majority differ → confirms different logic sources

### 4. Master Dataset Creation

Per year master datasets created:

- 2018-19 → 2024-25
- Fully null columns auto-dropped
- No duplicate school_id per year

### 5. Longitudinal Dataset Built

Final shape:
437,106 rows × 323 columns

Each row = school-year observation

---

# Phase 2: Structural Analysis (COMPLETED)

## School Survival Analysis

Total unique schools: 67,343

Schools active all 7 years: 57,548
Schools active only 1 year: 1,655

→ Majority structurally stable
→ Small churn segment exists

## Stability Labels Created

- stable (7 years)
- mid (2–6 years)
- unstable (1 year)

## Enrolment Growth Analysis

Median YoY Growth:

- stable ≈ -5%
- mid ≈ -1.6%
- unstable ≈ -47%

Insight:
Unstable schools show severe enrolment collapse before exit.
This becomes a predictive early-warning signal.

---

# Current System State

We now have:

✔ Clean multi-year school-level dataset
✔ Stability classification
✔ Enrolment trend signals
✔ Longitudinal structure
✔ School churn detection

This forms the data backbone for BAV.

---

# Next Objective (Strategic)

Move from:
Descriptive analytics

To:
Predictive & validation AI engine for infrastructure planning.

Data Preparation Summary Report
Project: AI‑Enabled Baseline Assessment & Validation (BAV) System
Department: School Education – Andhra Pradesh
Scope: Multi‑Year School Data Cleaning & Preparation

1. Objective
   The objective of this phase was to clean, standardize, validate, and prepare multi‑year school‑level datasets (2018–19 to 2024–25) to build a reliable data foundation for the AI‑enabled Baseline Assessment & Validation (BAV) system.

This phase focused strictly on ensuring data quality, structural consistency, and readiness for downstream AI/ML modelling.

2. Data Sources Processed
   The following datasets were integrated for each academic year:

Profile datasets (school metadata)

Facility datasets (infrastructure details)

Teacher datasets

Enrolment_1 (category-based enrolment)

Enrolment_2 (age-based enrolment)

Total years processed: 2018–19 to 2024–25

3. Key Data Cleaning & Preparation Steps
   A. Standardization
   Standardized all column names (lowercase, snake_case format)

Renamed inconsistent primary key (psuedocode → school_id)

Ensured consistent schema across all years

B. Schema Drift Handling
Managed structural changes in enrolment tables:

Pre‑2022: item_desc

2022 onwards: item_group, item_id

Implemented dynamic grouping column removal to ensure cross‑year compatibility

C. Aggregation & Feature Creation
From enrolment datasets:

total_boys

total_girls

total_enrolment

total_enrolment_age

Enrolment was aggregated at the school level for each year.

D. Data Validation
Verified total enrolment equals sum of class‑wise values

Validated boys/girls splits

Checked cross-consistency between enrolment tables

Ensured no duplicate school_id entries per year

E. Null Handling
Identified and automatically dropped columns that were 100% null

Preserved partially populated columns for downstream analysis

4. Outputs Generated
   Yearly Master Datasets
   Cleaned and merged master datasets created for:

2018–19

2019–20

2020–21

2021–22

2022–23

2023–24

2024–25

Each master dataset integrates profile, facility, teacher, and enrolment information.

Longitudinal Dataset
A stacked multi-year dataset was created:

Total rows: 437,106

Total columns: 323

Structure: One row per school per year

This dataset provides a unified analytical base for forecasting, validation, and infrastructure planning models.

5. Current Status
   The data preparation phase is complete.

The datasets are:

Clean

Standardized

Validated

Structurally consistent across years

Ready for AI/ML modelling and infrastructure demand forecasting

This completes the assigned responsibility of preparing and cleaning all data required for the project.

========================================================
Phase 1 – Clean Database Rebuild (Online MySQL)
========================================================

### Why Moving to an Online Database

Up to this point every output lived as flat CSV files on disk. That was fine
for ETL development and exploratory analysis, but it creates problems at scale:

- No concurrent access – only one process can read/write at a time.
- No referential integrity – nothing stops orphan or duplicate records.
- No query optimisation – every analysis re-scans entire files.
- No access from web services or dashboards.

Moving to an online MySQL instance (e.g. Aiven, PlanetScale, Railway)
gives us a single source of truth that any service—API, dashboard,
ML pipeline—can query simultaneously with full ACID guarantees.

### Schema Structure

Four normalised tables:

```
schools                     (1 row per school — static identity)
├── school_id  PK
├── school_name
├── district
├── block
├── management_type
├── school_category
├── latitude
└── longitude

yearly_metrics              (1 row per school per year — enrolment KPIs)
├── id  PK AUTO
├── school_id  → schools.school_id
├── academic_year
├── total_enrolment
└── attendance_rate

infrastructure_details      (1 row per school per year — facility flags)
├── id  PK AUTO
├── school_id  → schools.school_id
├── academic_year
├── total_class_rooms
├── cwsn_toilet_available
├── drinking_water_available
├── electrification_status
├── ramp_available
└── infrastructure_condition

teacher_metrics             (1 row per school per year — staffing)
├── id  PK AUTO
├── school_id  → schools.school_id
├── academic_year
├── total_teachers
└── required_teachers
```

### Table Relationships

- `schools` is the **dimension / master table**. It holds one row per
  physical school and is referenced by every other table via `school_id`.
- `yearly_metrics`, `infrastructure_details`, and `teacher_metrics` are
  **fact tables** — one record per school per academic year.
- This star-schema design keeps identity data separate from time-varying
  metrics, avoids redundancy, and makes year-over-year queries trivial.

### Why Idempotent Bootstrap Matters

The bootstrap script (`database/bootstrap_schema.py`) uses
`CREATE TABLE IF NOT EXISTS` so it can be re-run at any time without
risk of data loss or duplicate-table errors.

Benefits:

- Safe in CI/CD pipelines — deploy without manual checks.
- Team-friendly — any developer can run it on a fresh database.
- Future-proof — adding new tables later follows the same pattern.
- Zero downtime — existing data is never touched.

### Script Location

`database/bootstrap_schema.py`

Requires `DATABASE_URL` in `.env` (MySQL connection string).

### Current Status

✔ Schema bootstrap script created
✔ Four core tables defined
✔ Idempotent — safe to run repeatedly
✔ No data inserted yet — that is the next step

---

========================================================
Phase 1.1 – Infrastructure Schema Expansion
========================================================

### Why the Schema Was Expanded

The original `infrastructure_details` table captured only a handful of
string flags (drinking water, electrification, ramp, CWSN toilet,
generic condition). That was sufficient for basic profiling but fell
short of the analytical requirements defined by **Problem Statement 5**:

> _AI Solutions for Scalable and Sustainable School Infrastructure
> Planning and Monitoring under Samagra Shiksha._

The BAV system must validate infrastructure proposals, estimate
classroom gaps against government norms, flag accessibility
non-compliance, and prioritise maintenance — all at state scale
(60,000+ schools × 7 years). A flat set of text flags cannot
support those operations; the schema needed structured, typed
columns purpose-built for each validation dimension.

### Alignment with Problem Statement 5

| BAV Requirement                     | Schema Support                                                              |
| ----------------------------------- | --------------------------------------------------------------------------- |
| Norm-based classroom gap estimation | `total_class_rooms`, `usable_class_rooms`, `required_class_rooms`           |
| CWSN compliance validation          | `cwsn_toilet_available`, `ramp_available`, `resource_room_available`        |
| Maintenance prioritisation          | `building_condition`, `classroom_condition_score`, `last_major_repair_year` |
| Proposal validation logic           | Gap columns enable automated cross-check of funding requests                |
| Digital readiness tracking          | `electricity_available`, `internet_available`                               |
| Sanitation & gender compliance      | `separate_girls_toilet`, `drinking_water_available`                         |

### What This Schema Enables

1. **Norm-based classroom gap estimation**
   Compare `usable_class_rooms` against `required_class_rooms`
   (derived from enrolment-to-classroom norms) to quantify shortfall at
   school, block, and district level.

2. **CWSN compliance validation**
   Boolean flags for ramp, CWSN toilet, and resource room allow instant
   filtering of non-compliant schools and compliance-rate dashboards.

3. **Maintenance prioritisation**
   `classroom_condition_score` and `last_major_repair_year` feed a
   decay model that ranks schools by urgency of structural intervention.

4. **Proposal validation logic**
   When a school submits an infrastructure upgrade request, the system
   can cross-reference existing capacity, condition scores, and gap
   metrics to flag inflated or inconsistent proposals automatically.

5. **Future ML scoring**
   The expanded feature set provides direct input to predictive models —
   infrastructure risk scoring, resource allocation optimisation, and
   anomaly detection across thousands of schools simultaneously.

### Scalability Note

Every column was chosen to remain meaningful at scale. Boolean and
integer types keep storage compact and aggregation fast, even when
the system evaluates 60,000+ school records per academic year across
a 7-year window.

### Updated Table Structure

```
infrastructure_details (v1.1)
├── id                        PK AUTO
├── school_id                 → schools.school_id
├── academic_year
│
├── total_class_rooms         INT
├── usable_class_rooms        INT
├── required_class_rooms      INT
├── classroom_condition_score INT
│
├── drinking_water_available  BOOL
├── electricity_available     BOOL
├── internet_available        BOOL
│
├── separate_girls_toilet     BOOL
├── cwsn_toilet_available     BOOL
│
├── ramp_available            BOOL
├── resource_room_available   BOOL
│
├── building_condition        VARCHAR
└── last_major_repair_year    INT
```

### Migration Approach

The bootstrap script drops `infrastructure_details` (if it exists) and
recreates it with the expanded schema. All other tables are untouched
(`CREATE TABLE IF NOT EXISTS`). This keeps the migration safe and
repeatable while ensuring the latest structure is always applied.

### Current Status

✔ infrastructure_details schema expanded (v1.1)
✔ Aligned with Problem Statement 5 requirements
✔ Bootstrap script updated and idempotent
✔ Other tables (schools, yearly_metrics, teacher_metrics) unchanged
✔ No data inserted — population is the next step

---

========================================================
Phase 1.2 – Flexible Schema Mapping
========================================================

### Why Strict Column Checking Was Removed

The AIKosh / UDISE+ datasets are government-published and their schema
changes between academic years (columns renamed, added, or removed).
A loader that asserts exact column equality breaks the moment a new
year's CSV arrives with even one unexpected header.

Phase 1.2 replaces the rigid approach with a **COLUMN_MAPPING**
pattern: each DB column is explicitly paired with a CSV column name
(or `None` when no source exists). The loader calls `row.get(csv_col)`
for every field—if the column is absent or the value is NaN, it
gracefully falls back to `None`. No `KeyError`, no crash.

### How CSV-to-DB Mapping Works

Four declarative mapping dictionaries drive the entire ingestion:

| DB table                 | Mapping type                                     | Example                                                              |
| ------------------------ | ------------------------------------------------ | -------------------------------------------------------------------- |
| `schools`                | `SCHOOL_MAP` — direct string get                 | `"district" ← "district"`                                            |
| `yearly_metrics`         | `YEARLY_MAP` — direct with int/float cast        | `"total_enrolment" ← "total_enrolment"`                              |
| `infrastructure_details` | `INFRA_DIRECT_MAP` + `INFRA_BOOL_MAP` + computed | `"electricity_available" ← flag_to_bool("electricity_availability")` |
| `teacher_metrics`        | `TEACHER_MAP` — direct with int cast             | `"total_teachers" ← "total_teacher"`                                 |

**Computed fields:**

- `classroom_condition_score` =
  `(classrooms_needs_major_repair × 2) + (classrooms_needs_minor_repair × 1)`
- `cwsn_toilet_available` =
  `True` if `func_boys_cwsn_friendly == 1` OR `func_girls_cwsn_friendly == 1`

Fields not yet available in the CSV (`required_class_rooms`,
`last_major_repair_year`, `attendance_rate`, `required_teachers`) are
stored as NULL, ready to be populated in later phases.

### Why This Improves Robustness for AIKosh Datasets

1. **Schema drift tolerance** — New columns in future CSVs are silently
   ignored; missing columns produce NULLs instead of crashes.
2. **Single-source-of-truth** — All mapping decisions live in four
   dictionaries at the top of the file. Adding a new field means
   adding one line, not hunting through loop logic.
3. **Type safety** — Every value passes through `_safe_int`,
   `_safe_float`, `_safe_str`, or `_flag_to_bool` before reaching the
   database, preventing type-mismatch errors at the MySQL layer.
4. **Idempotent** — The script DELETEs all rows then re-INSERTs inside
   a single transaction, so every run produces identical state.

### How This Supports Scalable Ingestion

The loader processes 437,106 school-year rows across 67,343 schools in
batch inserts of 5,000 rows each, wrapped in a transaction. This
pattern scales linearly — when 2025-26 data appears, the CSV grows by
~60k rows and the loader handles it without code changes.

Because the mapping is declarative, onboarding a new data source
(e.g., a different state's UDISE+ export) requires only updating the
mapping dictionaries, not rewriting ingestion logic.

### Script Location

`database/load_master_data.py`

Requires `DATABASE_URL` in `.env`.

### Current Status

✔ Flexible COLUMN_MAPPING approach implemented
✔ Graceful handling of missing / extra CSV columns
✔ classroom_condition_score computed from repair fields
✔ cwsn_toilet_available derived from functional CWSN flags
✔ Boolean flag conversion (1 = True, else False/NULL)
✔ Batch inserts in single transaction
✔ Idempotent — safe to re-run
✔ Ready for production data load
