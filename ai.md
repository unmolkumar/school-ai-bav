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

---

========================================================
Phase 2 – Infrastructure Gap Engine (Samagra Shiksha Norm-Based)
========================================================

### Andhra Pradesh Samagra Shiksha Classroom Norms

The Department of School Education, Andhra Pradesh, follows the
Samagra Shiksha Abhiyaan classroom adequacy norms. These prescribe
maximum students per classroom by school level:

| Level            | Classes | Norm (students/classroom) |
| ---------------- | ------- | ------------------------- |
| Primary          | 1–5     | 30                        |
| Upper Primary    | 6–8     | 35                        |
| Secondary        | 9–10    | 40                        |
| Senior Secondary | 11–12   | 40                        |

### How Norms Vary by School Category (UDISE+ Codes)

Schools in the UDISE+ dataset carry a numeric `school_category` code.
Each code maps to a class range. Where a school spans multiple levels
(e.g., Category 2 = Classes 1–8), grade-wise enrolment breakdowns are
not available in the current dataset. In such cases a **conservative
blended norm of 30** (the strictest applicable standard) is applied to
avoid underestimating classroom requirements.

| UDISE+ Code | Structure                                | Norm Applied |
| ----------- | ---------------------------------------- | ------------ |
| 1           | Primary (1–5)                            | 30           |
| 2           | Primary + Upper Primary (1–8)            | 30 (blended) |
| 3           | Primary to Higher Secondary (1–12)       | 30 (blended) |
| 4           | Upper Primary only (5–8)                 | 35           |
| 5           | Upper Primary to Higher Secondary (6–12) | 35           |
| 6           | Primary to Secondary (1–10)              | 30 (blended) |
| 7           | Upper Primary to Secondary (6–10)        | 35           |
| 8           | Secondary only (9–10)                    | 40           |
| 10          | Secondary to Higher Secondary (9–12)     | 40           |
| 11          | Higher Secondary only (11–12)            | 40           |

**Blended norm assumption:**
When a school spans primary and higher levels, grade-wise enrolment
splits are not separately available. The conservative norm of 30 is
used to ensure no school is incorrectly classified as having surplus
classrooms. This assumption is documented here and can be refined
when grade-wise data becomes available.

### Computation Logic

```
required_class_rooms = ceil(total_enrolment / norm)
classroom_gap = max(required_class_rooms - usable_class_rooms, 0)
```

- `usable_class_rooms` is sourced from `classrooms_in_good_condition`
  (loaded in Phase 1.2).
- If `usable_class_rooms` is NULL, the full `required_class_rooms`
  is treated as the gap.
- Surplus classrooms are recorded as gap = 0 (not negative).

### Why Norm-Based Gap Estimation Is Critical for BAV

The BAV system must validate whether a school's infrastructure
proposal is justified. Without a norm-based baseline, there is no
objective reference to compare against. This engine provides that
baseline:

- **Gap = 0** → School meets classroom adequacy norms.
- **Gap > 0** → School has a quantified deficit that justifies a
  classroom construction request.
- **Large gap** → High-priority candidate for infrastructure funding.

### How This Enables Evidence-Based Prioritisation

1. **District-level ranking** — Aggregate `classroom_gap` by district
   to identify the most under-resourced regions.
2. **Block-level drill-down** — Same aggregation at block level for
   targeted allocation.
3. **Year-over-year tracking** — Gaps are computed per academic year,
   enabling trend analysis (are gaps widening or closing?).
4. **Proposal cross-validation** — When a school requests 10 new
   classrooms but the computed gap is 3, the request can be flagged
   for review.

### Alignment with Department of School Education Guidelines

This implementation directly supports the Department of School
Education's mandate under Samagra Shiksha to ensure:

- Every school meets minimum classroom adequacy standards.
- Infrastructure investment is directed where deficits are greatest.
- Proposals are validated against objective, reproducible metrics.
- Progress is measurable year over year.

### Script Location

`engines/infrastructure_gap_engine.py`

Requires `DATABASE_URL` in `.env`.

### Schema Update

`classroom_gap` (INT) column added to `infrastructure_details` via
ALTER TABLE IF NOT EXISTS logic in the engine, and also added to
`database/bootstrap_schema.py` for new deployments.

### Current Status

✔ Samagra Shiksha norms implemented for all 10 UDISE+ categories
✔ Conservative blended norm (30) used where grade-wise data unavailable
✔ required_class_rooms and classroom_gap computed and stored
✔ Top-10 district deficit ranking generated
✔ Idempotent — safe to re-run
✔ Transaction-wrapped batch updates
✔ Production-ready and scalable across 60,000+ schools

---

========================================================
Phase 2 Optimization – Indexing for Scalable Joins
========================================================

### Why Composite Indexes Are Required

The infrastructure gap engine performs a three-table JOIN
(`infrastructure_details` ↔ `yearly_metrics` ↔ `schools`) during its
bulk UPDATE. Without indexes, MySQL must execute full table scans on
each table for every join condition, comparing every row against every
other row.

With 437,000+ rows in each fact table, an un-indexed join produces
hundreds of billions of comparisons. Composite indexes on the join
keys allow MySQL to use B-tree lookups instead, reducing the operation
from $O(n^2)$ to $O(n \log n)$.

### Indexes Created

| Index Name               | Table                    | Columns                      | Purpose                                        |
| ------------------------ | ------------------------ | ---------------------------- | ---------------------------------------------- |
| `idx_infra_school_year`  | `infrastructure_details` | `(school_id, academic_year)` | Accelerates JOIN with `yearly_metrics`         |
| `idx_yearly_school_year` | `yearly_metrics`         | `(school_id, academic_year)` | Accelerates JOIN with `infrastructure_details` |
| `idx_schools_school_id`  | `schools`                | `(school_id)`                | Accelerates JOIN to dimension table            |

All indexes are created with safe execution — if an index already
exists, the error is caught and the engine continues. This preserves
idempotent behavior.

### Why JOIN Performance Degrades Without Indexing

MySQL's query optimizer cannot use an efficient join strategy (e.g.,
nested-loop with index lookup or hash join) when no index covers the
join columns. The result is:

- **Full table scans** on both sides of the join.
- **Temporary tables** spilled to disk for intermediate results.
- **Query time** scaling quadratically with row count.

For the BAV system's current dataset (~437k rows per fact table),
an un-indexed bulk UPDATE can take minutes. With indexes, the same
operation completes in seconds.

### Scalability to Millions of Rows

As additional years of UDISE+ data are ingested (or if the system is
extended to other states), row counts will grow into the millions.
Composite indexes ensure that:

- The bulk UPDATE remains $O(n \log n)$.
- Summary aggregation queries (`GROUP BY district`) use indexed
  lookups rather than full scans.
- The engine remains production-viable without architectural changes.

### No Business Logic Changed

This optimization is purely structural. The Samagra Shiksha classroom
norms, `required_class_rooms` calculation, `classroom_gap` formula,
idempotent behavior, and all output formats remain identical to
Phase 2.

### Current Status

✔ Three performance indexes added (safe / idempotent creation)
✔ Bulk UPDATE execution time logged
✔ No business logic modified
✔ Engine scalable to millions of rows

---

========================================================
Phase 3 – Teacher Adequacy Engine (Samagra Shiksha PTR Norms)
========================================================

### Official Pupil-Teacher Ratio (PTR) Norms

The Teacher Adequacy Engine uses PTR norms mandated under Indian
education policy as implemented by the Andhra Pradesh Department of
School Education under the Samagra Shiksha Abhiyaan.

**Policy Sources:**

1. **Right to Education Act, 2009** — Section 25 read with the
   Schedule prescribes maximum PTR for elementary schools:
   - Primary (Classes 1–5): PTR ≤ 30:1
   - Upper Primary (Classes 6–8): PTR ≤ 35:1
     (with subject-specific teachers required)

2. **Samagra Shiksha Framework for Implementation (MHRD, 2018)** —
   The integrated framework merges SSA, RMSA, and Teacher Education
   schemes. It inherits the RTE norms for elementary and the RMSA
   norms for secondary and senior secondary levels.

3. **Rashtriya Madhyamik Shiksha Abhiyan (RMSA) Framework** —
   Prescribes PTR ≤ 30:1 for secondary schools (Classes 9–10),
   with a minimum staffing of 1 Head Master + 5 subject teachers.

4. **AP Department of School Education** — The state implements
   central Samagra Shiksha PTR norms for teacher adequacy
   assessment across all government and aided schools.

### PTR Norms by Level

| Level            | Classes | PTR Norm | Source          |
| ---------------- | ------- | -------- | --------------- |
| Primary          | 1–5     | 30:1     | RTE Act, 2009   |
| Upper Primary    | 6–8     | 35:1     | RTE Act, 2009   |
| Secondary        | 9–10    | 30:1     | RMSA / Samagra  |
| Senior Secondary | 11–12   | 30:1     | Samagra Shiksha |

### How PTR Norms Map to UDISE+ School Categories

| UDISE+ Code | Structure                                | PTR Applied | Rationale                     |
| ----------- | ---------------------------------------- | ----------- | ----------------------------- |
| 1           | Primary (1–5)                            | 30          | Pure primary — RTE norm       |
| 2           | Primary + Upper Primary (1–8)            | 30          | Blended — conservative        |
| 3           | Primary to Higher Secondary (1–12)       | 30          | Blended — conservative        |
| 4           | Upper Primary only (5–8)                 | 35          | Pure upper primary — RTE norm |
| 5           | Upper Primary to Higher Secondary (6–12) | 30          | Blended — conservative        |
| 6           | Primary to Secondary (1–10)              | 30          | Blended — conservative        |
| 7           | Upper Primary to Secondary (6–10)        | 30          | Blended — conservative        |
| 8           | Secondary only (9–10)                    | 30          | Pure secondary — RMSA norm    |
| 10          | Secondary to Higher Secondary (9–12)     | 30          | Pure secondary/SS — RMSA      |
| 11          | Higher Secondary only (11–12)            | 30          | Pure SS — Samagra Shiksha     |

### Handling of Multi-Category (Blended) Schools

When a school spans multiple levels (e.g., Category 2 = Classes 1–8),
grade-wise enrolment breakdowns are not available in the current
dataset. In such cases the **conservative PTR of 30** (the stricter
standard) is applied. A lower PTR demands more teachers per student,
ensuring no school is incorrectly classified as having adequate
staffing.

Only **Category 4** (pure upper primary, Classes 5–8) receives the
higher PTR of 35:1, because all enrolled students fall exclusively
within the upper primary level where the RTE Act explicitly permits
this ratio due to subject-specialist staffing.

### Computation Logic

```
required_teachers = CEIL(total_enrolment / PTR_norm)
teacher_gap       = GREATEST(required_teachers - total_teachers, 0)
```

- `total_enrolment` is sourced from `yearly_metrics`.
- `total_teachers` is sourced from `teacher_metrics` (loaded in Phase 1.2).
- If `total_teachers` is NULL, the full `required_teachers` is treated
  as the gap.
- Surplus teachers are recorded as gap = 0 (not negative).

### Batched Execution Strategy

The engine batches the bulk UPDATE by academic year, executing one
UPDATE per year (~63k rows each). This prevents Railway MySQL from
timing out on large single-statement transactions and keeps each
commit boundary small.

Pattern:

```
for each academic_year:
    UPDATE teacher_metrics t
    JOIN yearly_metrics y ON ...
    JOIN schools s ON ...
    SET t.required_teachers = CEIL(y.total_enrolment / PTR_CASE),
        t.teacher_gap = GREATEST(CEIL(...) - IFNULL(t.total_teachers, 0), 0)
    WHERE t.academic_year = :year
```

### Indexing

A new composite index is created on `teacher_metrics`:

| Index Name                | Table             | Columns                      |
| ------------------------- | ----------------- | ---------------------------- |
| `idx_teacher_school_year` | `teacher_metrics` | `(school_id, academic_year)` |

Existing indexes from Phase 2 are reused:

- `idx_yearly_school_year` on `yearly_metrics`
- `idx_schools_school_id` on `schools`

All index creation is idempotent (no failure if index already exists).

### Scalability

The engine performs zero row fetches into Python. All computation
runs server-side inside MySQL. The batched-per-year approach keeps
each transaction at ~63k rows, well within Railway connection limits.
With indexes, the three-table JOIN operates at O(n log n). The
engine scales to millions of rows without architectural changes.

### Schema Update

`teacher_gap` (INT) column added to `teacher_metrics` via
ALTER TABLE logic in the engine, and also added to
`database/bootstrap_schema.py` for new deployments.

### Current Status

✔ Samagra Shiksha PTR norms implemented for all 10 UDISE+ categories
✔ Conservative blended PTR (30) used where grade-wise data unavailable
✔ Only pure upper primary (Category 4) uses PTR 35
✔ required_teachers and teacher_gap computed and stored
✔ Top-10 district teacher-deficit ranking generated
✔ Batched per academic year for Railway performance
✔ New index on teacher_metrics + reuses Phase 2 indexes
✔ Idempotent — safe to re-run
✔ No Phase 2 business logic modified

---

========================================================
Phase 4 — Composite Compliance Risk Engine
========================================================

### Policy Rationale

The Samagra Shiksha Abhiyaan framework requires state-level education
authorities to assess school readiness across multiple dimensions
simultaneously — teacher adequacy, infrastructure capacity, and
enrolment dynamics. Individual gap metrics (Phase 2: classroom gap,
Phase 3: teacher gap) are necessary but insufficient for governance
decision-making: a school may have adequate classrooms but critically
few teachers, or vice versa. The Composite Compliance Risk Engine
integrates these signals into a single, interpretable risk score that
enables district- and state-level prioritisation.

This approach aligns with the Samagra Shiksha Framework for
Implementation (MHRD, 2018), which mandates integrated planning
across teacher deployment (Chapter 5), civil works (Chapter 4), and
enrolment monitoring (Chapter 3). The framework explicitly calls for
"convergent planning" where resource allocation decisions consider
multiple school-level indicators rather than isolated metrics.

### Composite Risk Score Formula

$$
\text{risk\_score} = (0.45 \times \text{teacher\_deficit\_ratio}) + (0.35 \times \text{classroom\_deficit\_ratio}) + (0.20 \times \text{growth\_scaled})
$$

Where:

$$
\text{teacher\_deficit\_ratio} = \min\left(\frac{\text{teacher\_gap}}{\text{required\_teachers}}, 1.0\right)
$$

$$
\text{classroom\_deficit\_ratio} = \min\left(\frac{\text{classroom\_gap}}{\text{required\_class\_rooms}}, 1.0\right)
$$

$$
\text{enrolment\_growth\_rate} = \frac{\text{current\_enrolment} - \text{previous\_enrolment}}{\text{previous\_enrolment}} \quad \text{(via SQL LAG())}
$$

$$
\text{growth\_scaled} = \min(|\text{enrolment\_growth\_rate}|, 0.50)
$$

### Weight Justification (0.45 / 0.35 / 0.20)

| Weight | Component               | Justification                                                                                                                                                                                                                                                                                                                                                                    |
| ------ | ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0.45   | Teacher deficit ratio   | The RTE Act, 2009 identifies teacher adequacy (Section 25) as the primary input quality determinant. Empirical education research consistently shows PTR as the strongest predictor of learning outcomes in government schools. Teacher shortage directly impacts instructional hours and pedagogical quality.                                                                   |
| 0.35   | Classroom deficit ratio | Samagra Shiksha infrastructure norms treat classroom capacity as the core physical constraint. Overcrowded classrooms degrade learning environments and violate the RTE Act's stipulation of adequate space. Ranked second because temporary arrangements (shift systems) can partially mitigate classroom shortfalls, whereas teacher shortfalls have no equivalent workaround. |
| 0.20   | Enrolment growth (abs)  | Enrolment trajectory is a lagging indicator — it reflects emerging demand pressure (positive growth) or institutional decline risk (negative growth). Weighted lowest because it signals future risk rather than current non-compliance. The absolute value ensures both rapid growth (overcrowding risk) and rapid decline (closure risk) contribute to the risk assessment.    |

### Why Deficit Ratios Are Capped at 1.0

A school missing 10 teachers out of 5 required has a raw ratio of 2.0,
but in governance terms the school is fully non-compliant regardless of
whether the ratio is 1.0 or 5.0. Capping at 1.0 prevents extreme
outliers from distorting the composite score and ensures the weighted
sum remains in the interpretable [0, 1] range.

### Why Growth Is Capped at 0.50

Enrolment changes exceeding 50% year-over-year typically reflect
administrative events (school mergers, boundary redistricting, data
corrections) rather than organic demand shifts. Capping at 0.50
prevents these administrative artefacts from overwhelming the
composite score while preserving the signal from genuine growth or
decline trends.

### Safe Division

All division uses `NULLIF(denominator, 0)` to return NULL instead of
raising a division-by-zero error. `IFNULL(..., 0)` wraps the result
so that schools with zero requirements receive a deficit ratio of 0.

### Enrolment Growth via LAG()

Growth rate is computed using the SQL `LAG()` window function:

```sql
LAG(total_enrolment) OVER (
    PARTITION BY school_id ORDER BY academic_year
) AS prev_enrolment
```

For the first year of a school's record (no previous year exists),
`prev_enrolment` is NULL and `enrolment_growth_rate` defaults to 0.
This avoids penalising new schools for missing historical data.

### Risk Classification

| Score Range | Risk Level | Governance Interpretation                                   |
| ----------- | ---------- | ----------------------------------------------------------- |
| 0.00–0.20   | LOW        | School meets or nearly meets norms; routine monitoring only |
| 0.21–0.50   | MODERATE   | Partial compliance gaps; scheduled intervention recommended |
| 0.51–0.75   | HIGH       | Significant deficits; priority resource allocation required |
| > 0.75      | CRITICAL   | Severe multi-dimensional non-compliance; immediate action   |

These thresholds align with standard risk-stratification practice in
public administration. The CRITICAL tier (>0.75) identifies schools
where both teacher and infrastructure deficits are simultaneously
severe — precisely the population that Samagra Shiksha convergent
planning is designed to address.

### Schema Additions

Five columns added to `infrastructure_details` via ALTER TABLE:

| Column                    | Type        | Source                                           |
| ------------------------- | ----------- | ------------------------------------------------ |
| `classroom_deficit_ratio` | FLOAT       | classroom_gap / required_class_rooms, capped 1.0 |
| `teacher_deficit_ratio`   | FLOAT       | teacher_gap / required_teachers, capped 1.0      |
| `enrolment_growth_rate`   | FLOAT       | LAG()-based YoY growth from yearly_metrics       |
| `risk_score`              | FLOAT       | Weighted composite (0.45 + 0.35 + 0.20)          |
| `risk_level`              | VARCHAR(20) | CASE-classified: LOW/MODERATE/HIGH/CRITICAL      |

### Batched Execution Strategy

The engine executes three batched UPDATE passes per academic year:

1. **Deficit ratios** — JOIN infrastructure_details ↔ teacher_metrics
   to compute both deficit ratios in a single UPDATE.
2. **Growth rate** — JOIN infrastructure_details ↔ derived LAG()
   subquery from yearly_metrics.
3. **Risk score + level** — Pure self-UPDATE on infrastructure_details
   using the ratios computed in passes 1–2.

Each pass is batched by `WHERE academic_year = :year` (~63k rows per
batch), preventing Railway MySQL from timing out.

### Indexing

All four existing indexes are reused:

| Index Name                | Table                    | Purpose                        |
| ------------------------- | ------------------------ | ------------------------------ |
| `idx_infra_school_year`   | `infrastructure_details` | Target table + JOIN key        |
| `idx_teacher_school_year` | `teacher_metrics`        | JOIN for teacher_deficit_ratio |
| `idx_yearly_school_year`  | `yearly_metrics`         | LAG() subquery scan            |
| `idx_schools_school_id`   | `schools`                | District lookup in summary     |

### Scalability

All computation runs server-side inside MySQL. Zero rows are fetched
into Python. Three UPDATE passes × 7 years = 21 batched transactions,
each processing ~63k rows. With composite indexes, every JOIN operates
at O(n log n). The engine scales to millions of rows without
architectural changes.

### Script Location

`engines/compliance_risk_engine.py`

Requires `DATABASE_URL` in `.env`.
Depends on Phase 2 (classroom_gap) and Phase 3 (teacher_gap) being
run first.

### Current Status

✔ Composite risk formula implemented (0.45 / 0.35 / 0.20)
✔ Deficit ratios capped at 1.0 with safe division
✔ Enrolment growth via LAG() with NULL-safe defaults
✔ Growth capped at 0.50 to filter administrative noise
✔ Four-tier risk classification (LOW / MODERATE / HIGH / CRITICAL)
✔ Five new columns added to infrastructure_details
✔ Three batched UPDATE passes per academic year
✔ All existing indexes reused
✔ Idempotent — safe to re-run
✔ No Phase 2 or Phase 3 business logic modified

---

# ======================================================== Phase 5 — SCHOOL PRIORITISATION ENGINE

## Phase 5: School Prioritisation Engine

### Purpose

Converts raw risk scores (Phase 4) into actionable, policy-ready rankings
at both state and district level. Enables governance teams to identify
the most critical schools and allocate resources by priority tier.

### Architecture

Creates the `school_priority_index` table (one row per school per year).
All computation is server-side SQL with RANK(), PERCENT_RANK(), and LAG()
window functions. No Python row loops. Idempotent — safe to re-run.

### Computed Columns

| Column                      | Type        | Computation                                         |
| --------------------------- | ----------- | --------------------------------------------------- |
| `state_rank`                | INT         | RANK() OVER (ORDER BY risk_score DESC) per year     |
| `district_rank`             | INT         | RANK() OVER (PARTITION BY district ...) per year    |
| `priority_bucket`           | VARCHAR(20) | PERCENT_RANK → TOP_5 / TOP_10 / TOP_20 / STANDARD   |
| `persistent_high_risk_flag` | TINYINT     | 1 if 3+ consecutive years at HIGH or CRITICAL level |

### Priority Bucketing Logic

| Percentile (risk_score DESC) | Bucket   | Governance Interpretation       |
| ---------------------------- | -------- | ------------------------------- |
| ≤ 5%                         | TOP_5    | Immediate intervention required |
| ≤ 10%                        | TOP_10   | High-priority monitoring        |
| ≤ 20%                        | TOP_20   | Scheduled review recommended    |
| > 20%                        | STANDARD | Routine compliance monitoring   |

### Persistent High-Risk Detection

Uses LAG(risk_level, 1) and LAG(risk_level, 2) to check the current
year and two preceding years. If all three are HIGH or CRITICAL, the
flag is set to 1. This identifies chronically underperforming schools
that require structural intervention rather than incremental fixes.

### Indexing

| Index Name                 | Table                 | Purpose            |
| -------------------------- | --------------------- | ------------------ |
| `idx_priority_school_year` | school_priority_index | Primary lookup key |

### Verified Output (437,106 rows)

- Top 5% : 22,195
- Top 10% : 21,699
- Top 20% : 44,029
- Standard : 349,183
- Persistent high-risk: 10,588

Top districts: ASR (4,327 high-priority, 972 persistent),
KURNOOL (4,136 high-priority, 1,511 persistent).

### Script Location

`engines/prioritisation_engine.py`

### Current Status

✔ State & district ranking via RANK() window functions
✔ Priority bucketing via PERCENT_RANK() (TOP_5/TOP_10/TOP_20/STANDARD)
✔ Persistent high-risk flag via LAG() (3+ consecutive HIGH/CRITICAL)
✔ Batched per academic year (~63k rows/batch)
✔ Composite index on (school_id, academic_year)
✔ Idempotent — safe to re-run

---

# ======================================================== Phase 6 — BUDGET ALLOCATION SIMULATOR

## Phase 6: Budget Allocation Simulator

### Purpose

Simulates priority-ordered allocation of limited classroom and teacher
resources across all schools, enabling policy-makers to model the impact
of different budget levels before committing real funds.

### Architecture

Creates the `budget_simulation` table. Seeds from infrastructure_details

- teacher_metrics, ranks by risk_level priority (CRITICAL first), then
  uses cumulative SUM() OVER() to determine allocation cutoff points.
  All computation is server-side SQL. No Python row loops.

### Allocation Algorithm

1. **Seeding**: JOINs infrastructure_details × teacher_metrics × schools
   per year. Each school gets its classroom_gap and teacher_gap.
2. **Priority ordering**: ROW_NUMBER() with ORDER BY
   CRITICAL → HIGH → MODERATE → LOW, then by gap magnitude DESC.
3. **Cumulative allocation**: Cumulative SUM(classroom_gap) OVER
   (ORDER BY allocation_priority). Schools within budget ceiling get
   `classrooms_allocated = classroom_gap`. Same pattern for teachers.
4. **Resolution tracking**: `classroom_resolved` / `teacher_resolved`
   flags indicate whether the school's full deficit was covered.

### Configuration Defaults

| Parameter          | Default      | Derives                  |
| ------------------ | ------------ | ------------------------ |
| Classroom budget   | ₹500,000,000 | = 1,000 classrooms @ ₹5L |
| Cost per classroom | ₹500,000     |                          |
| Max classrooms     | 1,000        |                          |
| Teacher posts      | 10,000       |                          |

### Indexing

| Index Name               | Table             | Purpose                      |
| ------------------------ | ----------------- | ---------------------------- |
| `idx_budget_school_year` | budget_simulation | Primary lookup key           |
| `idx_budget_priority`    | budget_simulation | Allocation ordering per year |

### Verified Output (437,106 rows)

- Classrooms allocated: 7,000 (7 years × 1,000)
- Teachers allocated: 70,000 (7 years × 10,000)
- Schools classroom-resolved: 1,111
- Schools teacher-resolved: 6,389
- Remaining classroom deficit: 1,772,152
- Remaining teacher deficit: 1,653,961

### Script Location

`engines/budget_allocation_engine.py`

### Current Status

✔ Priority-ordered allocation (CRITICAL → HIGH → MODERATE → LOW)
✔ Cumulative window sum for budget cutoff
✔ Configurable budget parameters
✔ Resolution tracking per school
✔ Batched per academic year
✔ Idempotent — safe to re-run

---

# ======================================================== Phase 7 — LONGITUDINAL RISK TREND ENGINE

## Phase 7: Longitudinal Risk Trend Engine

### Purpose

Tracks how each school's risk profile evolves over time. Identifies
improving, stable, deteriorating, chronically-at-risk, and volatile
schools — enabling proactive rather than reactive governance.

### Architecture

Creates the `risk_trend` table (one row per school per year).
Inserts all years in a single pass to ensure LAG() windows operate
across the full time series. Then computes chronic and volatile
flags via batched UPDATE passes per year.

### Computed Columns

| Column                 | Type        | Computation                                        |
| ---------------------- | ----------- | -------------------------------------------------- | ---------- | ------------------------------- |
| `risk_delta`           | FLOAT       | current risk_score − LAG(risk_score, 1)            |
| `prev_risk_score`      | FLOAT       | LAG(risk_score, 1) for reference                   |
| `trend_direction`      | VARCHAR(20) | IMPROVING / STABLE / DETERIORATING / BASELINE      |
| `year_over_year_count` | INT         | ROW_NUMBER() — sequential year index per school    |
| `chronic_risk_flag`    | TINYINT     | 1 if 3+ consecutive years HIGH/CRITICAL            |
| `volatile_flag`        | TINYINT     | 1 if                                               | risk_delta | > 0.25 in current or prior year |
| `cumulative_avg_risk`  | FLOAT       | Running average of risk_score across all prior yrs |

### Trend Classification

| Condition         | Direction     | Governance Interpretation            |
| ----------------- | ------------- | ------------------------------------ |
| delta IS NULL     | BASELINE      | First year — no prior data           |
| delta < −0.10     | IMPROVING     | Meaningful reduction in risk         |
| abs(delta) ≤ 0.10 | STABLE        | No significant change                |
| delta > +0.10     | DETERIORATING | Risk increasing — requires attention |

### Chronic Risk Detection

Uses LAG(risk_level, 1) and LAG(risk_level, 2) from infrastructure_details
to check 3 consecutive years of HIGH or CRITICAL classification.
Matches the persistent_high_risk_flag from Phase 5 for cross-validation.

### Volatile Detection

A school is flagged volatile if |risk_delta| > 0.25 in the current or
previous transition. This catches schools with erratic risk profiles
that may indicate data quality issues or rapid environmental changes.

### Indexing

| Index Name              | Table      | Purpose                          |
| ----------------------- | ---------- | -------------------------------- |
| `idx_trend_school_year` | risk_trend | Primary lookup key               |
| `idx_trend_direction`   | risk_trend | Filter by year + trend direction |

### Verified Output (437,106 rows)

- BASELINE : 67,343 (first year — no prior data)
- IMPROVING : 123,487 (delta < −0.10)
- STABLE : 170,401 (abs(delta) ≤ 0.10)
- DETERIORATING : 75,875 (delta > +0.10)
- Chronic risk : 10,588 (3+ consecutive HIGH/CRITICAL)
- Volatile : 160,357 (|delta| > 0.25 recent)
- Mean cumulative avg risk: 0.3239

### Script Location

`engines/risk_trend_engine.py`

### Current Status

✔ Risk delta via LAG() across full time series
✔ Trend classification (IMPROVING / STABLE / DETERIORATING / BASELINE)
✔ Chronic risk flag (3+ consecutive HIGH/CRITICAL years)
✔ Volatile flag (|delta| > 0.25 in recent transitions)
✔ Running cumulative average risk per school
✔ Full longitudinal INSERT (LAG correctness preserved)
✔ Chronic + volatile flags batched per year
✔ Idempotent — safe to re-run

---

# ======================================================== Phase 8 — DISTRICT COMPLIANCE INDEX

## Phase 8: District Compliance Index

### Purpose

Aggregates school-level data up to the district level, producing a
single compliance scorecard per district per academic year. Enables
state-level monitoring and cross-district comparison.

### Architecture

Creates the `district_compliance_index` table (one row per district
per year). Uses GROUP BY with aggregate functions (COUNT, AVG, SUM),
then adds YoY improvement and district ranking via window functions
in separate UPDATE passes.

### Computed Columns

| Column                    | Type       | Computation                                     |
| ------------------------- | ---------- | ----------------------------------------------- |
| `total_schools`           | INT        | COUNT(DISTINCT school_id) per district-year     |
| `avg_risk_score`          | FLOAT      | AVG(risk_score) across district schools         |
| `pct_high_critical`       | FLOAT      | % of schools rated HIGH or CRITICAL             |
| `total_classroom_deficit` | INT        | SUM(classroom_gap) where gap > 0                |
| `total_teacher_deficit`   | INT        | SUM(teacher_gap) where gap > 0                  |
| `total_enrolment`         | BIGINT     | SUM(total_enrolment) from yearly_metrics        |
| `avg_classroom_condition` | FLOAT      | AVG(classroom_condition_score)                  |
| `yoy_risk_improvement`    | FLOAT      | LAG()-based change in avg_risk vs previous year |
| `district_rank`           | INT        | RANK() by avg_risk_score DESC per year          |
| `compliance_grade`        | VARCHAR(5) | A/B/C/D/F based on avg_risk thresholds          |

### Compliance Grading

| Avg Risk Score | Grade | Governance Interpretation            |
| -------------- | ----- | ------------------------------------ |
| ≤ 0.15         | A     | Meets norms comprehensively          |
| ≤ 0.30         | B     | Minor gaps — scheduled maintenance   |
| ≤ 0.50         | C     | Significant gaps — targeted action   |
| ≤ 0.75         | D     | Major non-compliance — urgent review |
| > 0.75         | F     | Systemic failure — structural reform |

### Indexing

| Index Name              | Table                     | Purpose               |
| ----------------------- | ------------------------- | --------------------- |
| `idx_dci_district_year` | district_compliance_index | Primary lookup key    |
| `idx_dci_rank`          | district_compliance_index | Filter by year + rank |

### Verified Output (182 records = 26 districts × 7 years)

- Overall avg risk score: 0.3019
- Avg % HIGH+CRITICAL: 19.23%
- Grand classroom deficit: 1,779,152
- Grand teacher deficit: 1,723,961
- Compliance grades: B=96, C=86, A/D/F=0

Top risk districts (2024-25): KURNOOL (#1, 0.3828, Grade C),
ASR (#2, 0.3557, Grade C), NANDYAL (#3, 0.3153, Grade C).

### Script Location

`engines/district_compliance_engine.py`

### Current Status

✔ Full district-level aggregation (schools, risk, deficits, enrolment)
✔ Compliance grading (A/B/C/D/F)
✔ YoY risk improvement via LAG()
✔ District ranking via RANK()
✔ Batched per academic year
✔ Idempotent — safe to re-run

---

# ======================================================== Phase 9 — PROPOSAL VALIDATION ENGINE

## Phase 9: Proposal Validation Engine

### Purpose

Validates school demand proposals (classroom and teacher requests) against
actual computed infrastructure and teacher gaps. Provides automated
decision support (ACCEPTED / FLAGGED / REJECTED) with confidence scores,
enabling governance teams to rapidly approve or challenge demand plans.

### Architecture

Creates two tables:

- `school_demand_proposals` — synthetic input proposals (with noise)
- `proposal_validations` — validated output with decisions

Proposals are generated using CRC32-based deterministic noise (±30%
around actual gap) to simulate realistic over/under-requesting.
Validation uses SQL CASE logic comparing requested amounts against
actual gaps.

### Decision Logic

| Condition                             | Decision | Reason Code            |
| ------------------------------------- | -------- | ---------------------- |
| No deficit but requesting resources   | REJECTED | NO_DEFICIT             |
| Request > 1.5× actual gap (classroom) | REJECTED | CLASSROOM_OVER_REQUEST |
| Request > 1.5× actual gap (teacher)   | REJECTED | TEACHER_OVER_REQUEST   |
| Request 1.2–1.5× actual gap           | FLAGGED  | \*\_MODERATE_OVER      |
| Request < 0.5× actual gap             | FLAGGED  | \*\_UNDER_REQUEST      |
| No request and no gap                 | ACCEPTED | NO_REQUEST             |
| Within ±20% tolerance                 | ACCEPTED | WITHIN_TOLERANCE       |

### Confidence Score

Confidence = max(0, 1.0 − (|1 − classroom_ratio| + |1 − teacher_ratio|) / 2)

A perfect match (ratio = 1.0) yields confidence = 1.0. Deviations
reduce confidence proportionally.

### Proposal Generation (Simulation)

Uses CRC32(CONCAT(school_id, academic_year, suffix)) to generate
deterministic pseudo-random noise factors between 0.7 and 1.5.
This ensures:

- Reproducibility across runs
- Realistic distribution of over/under-requesting
- No random() dependency or external data needed

### Indexing

| Index Name                    | Table                   | Purpose               |
| ----------------------------- | ----------------------- | --------------------- |
| `idx_proposals_school_year`   | school_demand_proposals | Primary lookup        |
| `idx_validations_school_year` | proposal_validations    | Primary lookup        |
| `idx_validations_decision`    | proposal_validations    | Filter by year+status |

### Verified Output (437,106 proposals)

- ACCEPTED : 325,758
- FLAGGED : 111,348
- REJECTED : 0
- Avg confidence: 0.916

Reason breakdown: WITHIN_TOLERANCE=200,608, NO_REQUEST=125,150.

### Script Location

`engines/proposal_validation_engine.py`

### Current Status

✔ Synthetic proposal generation via CRC32 deterministic noise
✔ Multi-dimensional validation (classroom + teacher)
✔ Three-tier decision (ACCEPTED / FLAGGED / REJECTED)
✔ Confidence scoring with ratio-based formula
✔ Reason codes for governance audit trail
✔ Batched per academic year
✔ Idempotent — safe to re-run

---

# ======================================================== Phase 10 — ENROLMENT FORECASTING ENGINE

## Phase 10: Enrolment Forecasting Engine

### Purpose

Projects future enrolment, classroom requirements, and teacher
requirements for each school using weighted moving-average growth
trends. Generates 3-year forward projections (T+1, T+2, T+3) from
the latest available year, enabling proactive capacity planning.

### Architecture

Creates the `enrolment_forecast` table (3 rows per school — one per
forecast year). Uses a single INSERT...SELECT with CROSS JOIN to
generate all 3 horizons simultaneously. Growth rates computed via
LAG() across the full time series before filtering to latest year.

### Growth Rate Computation

Weighted moving average of 3 most recent YoY growth rates:

growth = (3 × delta_1 + 2 × delta_2 + 1 × delta_3) / (6 × E_prev)

Where delta_k is the absolute enrolment change k years ago and
E_prev is the prior year's enrolment. Weights (3, 2, 1) give more
influence to recent trends.

Growth is capped at ±0.30 to prevent wild projections from
administrative anomalies (mergers, boundary changes).

### Projection Formula

E(t+n) = E(t) × (1 + g_hat)^n

Where g_hat is the capped growth rate and n is in {1, 2, 3}.

### UDISE+ Norms Applied

| School Category | Classroom Norm (students/room) | PTR Norm (students/teacher) |
| --------------- | ------------------------------ | --------------------------- |
| 1, 2, 3         | 30                             | 30                          |
| 4, 5            | 35                             | 30                          |
| 6, 7, 8, 10, 11 | 40                             | 35                          |

### Computed Columns

| Column                     | Type  | Computation                         |
| -------------------------- | ----- | ----------------------------------- |
| `base_enrolment`           | INT   | Enrolment in the latest year        |
| `avg_growth_rate`          | FLOAT | Weighted 3-year moving average      |
| `projected_enrolment`      | INT   | base × (1 + growth)^years_ahead     |
| `projected_classrooms_req` | INT   | CEILING(projected_enrolment / norm) |
| `projected_teachers_req`   | INT   | CEILING(projected_enrolment / PTR)  |
| `projected_classroom_gap`  | INT   | GREATEST(0, required − current)     |
| `projected_teacher_gap`    | INT   | GREATEST(0, required − current)     |

### Indexing

| Index Name            | Table              | Purpose                    |
| --------------------- | ------------------ | -------------------------- |
| `idx_forecast_school` | enrolment_forecast | Primary lookup key         |
| `idx_forecast_year`   | enrolment_forecast | Filter by forecast horizon |

### Verified Output (183,951 rows = 61,317 schools × 3 horizons)

- Base year: 2024-25
- Forecast range: 2025-26 → 2027-28
- Mean growth rate: −0.1469 (overall declining enrolment — realistic for AP)
- Avg projected enrolment: 271

Projected Classroom Deficit by Horizon:

- T+1: 200,719
- T+2: 218,586
- T+3: 247,764

Projected Teacher Deficit by Horizon:

- T+1: 209,829
- T+2: 232,862
- T+3: 268,040

Top deficit district (T+3): KURNOOL (cr_gap 18,541, tr_gap 20,100).

### Script Location

`engines/forecasting_engine.py`

### Current Status

✔ Weighted 3-year moving average growth rate
✔ LAG() across full time series (correct longitudinal window)
✔ 3-year forward projection (T+1, T+2, T+3)
✔ UDISE+ category-based classroom and PTR norms
✔ Growth capped at ±0.30 to filter anomalies
✔ Projected deficit computation against current capacity
✔ CROSS JOIN for efficient multi-horizon generation
✔ Idempotent — safe to re-run

---

# ======================================================== COMPLETE SYSTEM ARCHITECTURE

## System Architecture Summary (Phases 1-10)

### Execution Order and Dependencies

```
Phase 1: Schema Bootstrap           → Creates all tables
Phase 2: Infrastructure Gap Engine  → classroom_gap (requires Phase 1)
Phase 3: Teacher Adequacy Engine    → teacher_gap   (requires Phase 1)
Phase 4: Compliance Risk Engine     → risk_score    (requires Phases 2, 3)
Phase 5: Prioritisation Engine      → rankings      (requires Phase 4)
Phase 6: Budget Allocation Simulator → allocation   (requires Phases 2, 3, 4)
Phase 7: Risk Trend Engine          → trend/chronic  (requires Phase 4)
Phase 8: District Compliance Index  → district agg   (requires Phases 2, 3, 4)
Phase 9: Proposal Validation Engine → decisions      (requires Phases 2, 3)
Phase 10: Forecasting Engine        → projections    (requires Phase 1 data)
```

### Database Tables (11 total)

| Table                       | Phase | Rows  | Description                     |
| --------------------------- | ----- | ----- | ------------------------------- |
| `schools`                   | 1     | ~63k  | Static school master data       |
| `infrastructure_details`    | 1,2,4 | ~437k | Infrastructure + computed risk  |
| `teacher_metrics`           | 1,3   | ~437k | Teacher counts + computed gap   |
| `yearly_metrics`            | 1     | ~437k | Enrolment and attendance        |
| `school_priority_index`     | 5     | ~437k | Rankings + priority buckets     |
| `budget_simulation`         | 6     | ~437k | Resource allocation simulation  |
| `risk_trend`                | 7     | ~437k | Longitudinal risk tracking      |
| `district_compliance_index` | 8     | ~182  | District-level compliance cards |
| `school_demand_proposals`   | 9     | ~437k | Simulated demand proposals      |
| `proposal_validations`      | 9     | ~437k | Validated proposals + decisions |
| `enrolment_forecast`        | 10    | ~184k | 3-year forward projections      |
| `ml_enrolment_forecast`     | 11    | ~184k | ML-based 3-year projections     |

### Engineering Principles

1. **Zero Python loops** — all row-level computation via SQL
2. **Window functions** — RANK, PERCENT_RANK, LAG, ROW_NUMBER, cumulative SUM/AVG
3. **Batched execution** — ~63k rows per year-batch, within Railway limits
4. **Idempotent** — every engine safe to re-run (DELETE + re-INSERT or overwrite)
5. **Indexed** — composite indexes on (school_id, academic_year) across all tables
6. **UDISE+ compliant** — school_category-based norms for classrooms and PTR
7. **Policy-explainable** — every score, flag, and decision traceable to formula

---

## Phase 11 — ML-Based Enrolment Forecasting Engine

### Objective

Replace Phase 10's weighted moving-average (WMA) with a cross-school
GradientBoostingRegressor that learns non-linear enrolment dynamics
from ~300 k training samples across all schools and years.

### Why ML Over Per-School ARIMA

With only 7 annual data points per school, a per-school ARIMA(1,1,0)
is essentially computing a differenced trend line. A cross-school
Gradient Boosting model trains on ~300 k+ samples and captures:

- District-level demographic shifts
- Management-type effects on retention
- Non-linear interactions (gaps × school-type → enrolment change)
- Momentum / mean-reversion patterns across the full panel
- Feature importance insights for policy explanation

### Model Architecture

| Component     | Detail                                                 |
| ------------- | ------------------------------------------------------ |
| Algorithm     | sklearn GradientBoostingRegressor                      |
| Loss          | Huber (robust to outlier growth)                       |
| Target        | Growth rate: (next − current) / current, clipped ±0.30 |
| Features      | 20 features (see below)                                |
| Trees         | 500 (early-stop @ 30 no-change)                        |
| Depth         | 4, min_samples_leaf=100                                |
| Learning rate | 0.03                                                   |
| Subsample     | 0.8                                                    |
| Train filter  | Schools with enrolment ≥ 10                            |
| Projection    | Compound: base × (1 + g_ml)^k for k=1,2,3              |
| Calibration   | Post-prediction bias correction to training mean       |

### Feature Set (20 features)

| Feature                 | Type        | Source                                 |
| ----------------------- | ----------- | -------------------------------------- |
| total_enrolment         | Numeric     | yearly_metrics                         |
| enrolment_lag1, lag2    | Numeric     | Shifted enrolment                      |
| growth_rate             | Numeric     | (current − lag1) / lag1, clipped ±0.30 |
| growth_rate_lag1        | Numeric     | Previous year's growth, clipped        |
| school_category         | Categorical | schools                                |
| total_teachers          | Numeric     | teacher_metrics                        |
| total_class_rooms       | Numeric     | infrastructure_details                 |
| usable_class_rooms      | Numeric     | infrastructure_details                 |
| classroom_gap           | Numeric     | Phase 2 computed                       |
| teacher_gap             | Numeric     | Phase 3 computed                       |
| risk_score              | Numeric     | Phase 4 computed                       |
| teacher_deficit_ratio   | Numeric     | Phase 4 computed                       |
| classroom_deficit_ratio | Numeric     | Phase 4 computed                       |
| district_code           | Encoded     | LabelEncoder(district)                 |
| management_code         | Encoded     | LabelEncoder(management_type)          |
| enrolment_3yr_mean      | Numeric     | Rolling 3-year mean                    |
| enrolment_volatility    | Numeric     | Rolling 3-year std, capped at 500      |
| teacher_per_student     | Numeric     | teachers / enrolment                   |
| rooms_per_student       | Numeric     | usable_rooms / enrolment               |

### Feature Importance (Top 10)

| Feature              | Importance | Insight                                            |
| -------------------- | ---------- | -------------------------------------------------- |
| enrolment_volatility | 0.3974     | Volatile schools have predictable decline patterns |
| risk_score           | 0.1180     | Higher risk → different growth trajectory          |
| total_class_rooms    | 0.1178     | Infrastructure capacity affects retention          |
| enrolment_lag1       | 0.0798     | Previous enrolment level matters                   |
| growth_rate_lag1     | 0.0781     | Growth momentum effect                             |
| growth_rate          | 0.0769     | Current growth trajectory                          |
| management_code      | 0.0464     | Govt vs private affects retention                  |
| teacher_per_student  | 0.0333     | Better ratios → better retention                   |
| enrolment_lag2       | 0.0205     | 2-year-ago context                                 |
| rooms_per_student    | 0.0098     | Space adequacy signal                              |

### Train / Test Split

- Temporal: train on 2018-19 → 2022-23 transitions (302,774 samples, enrolment ≥ 10)
- Test on 2023-24 → 2024-25 transition (60,626 samples)

### Performance (ML vs Phase 10 WMA)

| Metric                | ML (GBR)  | Phase 10 (WMA) |
| --------------------- | --------- | -------------- |
| Enrolment R² (test)   | **0.926** | 0.903          |
| Enrolment MAE (test)  | **55**    | 56             |
| Enrolment MAPE (test) | 38.71%    | 30.27%         |
| Growth R² (train)     | 0.623     | —              |

- ML beats WMA on R² (+2.5%) and MAE (−1 student)
- MAPE is higher because ML is worse on very small schools (relative error amplified)
- At the aggregate / district level ML produces tighter, more realistic gap forecasts

### Projection Results

| Horizon | ML cr_gap | Phase 10 cr_gap | Δ       | ML tr_gap | Phase 10 tr_gap | Δ       |
| ------- | --------- | --------------- | ------- | --------- | --------------- | ------- |
| T+1     | 198,342   | 200,719         | −2,377  | 203,766   | 209,829         | −6,063  |
| T+2     | 207,348   | 218,586         | −11,238 | 212,437   | 232,862         | −20,425 |
| T+3     | 220,546   | 247,764         | −27,218 | 225,872   | 268,040         | −42,168 |

ML projections grow more conservatively (mean growth −0.023 vs WMA's implicit −0.15),
producing smaller gap forecasts at T+2 and T+3.

### Design Decisions

1. **Growth rate target (not absolute enrolment)**: Tree-based models can't learn
   the identity function (next ≈ current). Predicting the growth rate and
   compounding produces more stable results.

2. **Clipped features & target (±0.30)**: The raw growth distribution has
   std=0.70 with heavy right skew (school mergers, data errors). Clipping
   to ±0.30 matches Phase 10's cap and removes outlier influence.

3. **Compound projection (no autoregression)**: Feeding inflated T+1
   predictions back creates positive feedback loops (+70% growth). Compound
   projection uses one growth prediction for all horizons: base × (1+g)^k.

4. **Bias calibration**: Post-prediction shift ensures the forecast mean
   matches training data mean, preventing systematic over/under-prediction.

5. **Training filter (enrolment ≥ 10)**: Schools with <10 students have
   noise-dominated growth rates that degrade model quality.

6. **Huber loss**: Robust to remaining outliers in the clipped distribution,
   less sensitive to extreme residuals than MSE.

### Table Schema

| Column                   | Type        | Computation                              |
| ------------------------ | ----------- | ---------------------------------------- |
| school_id                | VARCHAR(50) | From schools table                       |
| base_year                | VARCHAR(20) | 2024-25                                  |
| forecast_year            | VARCHAR(20) | 2025-26 / 2026-27 / 2027-28              |
| years_ahead              | INT         | 1, 2, or 3                               |
| base_enrolment           | INT         | Enrolment in base year                   |
| ml_growth_rate           | FLOAT       | ML-predicted growth rate (clipped ±0.30) |
| projected_enrolment      | INT         | base × (1 + g_ml)^years_ahead            |
| projected_classrooms_req | INT         | CEILING(projected / cr_norm)             |
| projected_teachers_req   | INT         | CEILING(projected / ptr_norm)            |
| current_classrooms       | INT         | Current usable classrooms                |
| current_teachers         | INT         | Current total teachers                   |
| projected_classroom_gap  | INT         | MAX(0, required − current)               |
| projected_teacher_gap    | INT         | MAX(0, required − current)               |
| school_category          | INT         | UDISE+ category code                     |
| model_version            | VARCHAR(20) | 'v1.0'                                   |

### Indexing

| Index Name       | Table                 | Purpose              |
| ---------------- | --------------------- | -------------------- |
| idx_ml_fc_school | ml_enrolment_forecast | School + year lookup |
| idx_ml_fc_year   | ml_enrolment_forecast | Horizon filtering    |

### Script Location

`engines/ml_forecasting_engine.py`

### Current Status

✔ 20-feature GradientBoostingRegressor with huber loss
✔ Temporal train/test split (302k train, 60k test)
✔ Growth rate target clipped to ±0.30
✔ Feature clipping to prevent out-of-distribution extrapolation
✔ Post-prediction bias calibration
✔ Compound projection (no autoregressive divergence)
✔ R² = 0.926, MAE = 55 (beats Phase 10 WMA)
✔ Realistic growth forecasts (mean −0.023)
✔ Feature importance for policy explanation
✔ 183,951 forecast rows written (61,317 schools × 3 horizons)
✔ Idempotent — safe to re-run
