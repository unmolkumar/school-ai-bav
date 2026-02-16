"""
load_master_data.py

Phase 1.2 — Flexible Schema-Mapped Longitudinal Data Loader

Reads data/processed/master_longitudinal.csv and inserts normalised rows
into Railway MySQL (schools, yearly_metrics, infrastructure_details,
teacher_metrics).

Design principles:
  - Flexible COLUMN_MAPPING — no strict column-equality checks.
  - Missing CSV columns are silently treated as NULL.
  - Numeric flag codes (1/2) are converted to booleans.
  - classroom_condition_score is computed from repair columns.
  - Idempotent: DELETE-all + re-INSERT inside a single transaction.
"""

import os
import sys
import time

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ── Configuration ────────────────────────────────────────────────────────────

BATCH_SIZE = 5000
CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data", "processed", "master_longitudinal.csv",
)

# ── Column mappings  (DB column ← CSV column) ───────────────────────────────
# If a CSV column is missing, the value defaults to None.

SCHOOL_MAP = {
    "school_id":        "school_id",
    "school_name":      None,                    # not in CSV
    "district":         "district",
    "block":            "block",
    "management_type":  "managment",             # CSV spelling
    "school_category":  "school_category",
    "latitude":         None,                    # not in CSV
    "longitude":        None,                    # not in CSV
}

YEARLY_MAP = {
    "school_id":       "school_id",
    "academic_year":   "year",
    "total_enrolment": "total_enrolment",
    "attendance_rate": None,                     # not available yet
}

INFRA_DIRECT_MAP = {
    "school_id":            "school_id",
    "academic_year":        "year",
    "total_class_rooms":    "total_class_rooms",
    "usable_class_rooms":   "classrooms_in_good_condition",
    "building_condition":   "building_status",
}

# Boolean flag columns  (DB col → CSV col, where 1 = True)
INFRA_BOOL_MAP = {
    "drinking_water_available": "drinking_water_available",
    "electricity_available":    "electricity_availability",
    "internet_available":       "internet",
    "separate_girls_toilet":    "separate_girls_toilet",
    "ramp_available":           "availability_ramps",
    "resource_room_available":  "resource_room_available",
}

TEACHER_MAP = {
    "school_id":        "school_id",
    "academic_year":    "year",
    "total_teachers":   "total_teacher",
    "required_teachers": None,                   # not available yet
}

# ── Helpers ──────────────────────────────────────────────────────────────────


def _safe_int(value):
    """Return int if finite, else None."""
    if pd.isna(value):
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def _safe_float(value):
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _safe_str(value, max_len=255):
    if pd.isna(value):
        return None
    s = str(value).strip()
    return s[:max_len] if s else None


def _flag_to_bool(value, yes_value=1):
    """Convert a numeric flag (1 = Yes, 2 = No) to bool / None."""
    v = _safe_float(value)
    if v is None:
        return None
    return v == yes_value


def _get(row, csv_col):
    """Safely get a value from a row; returns None if column missing."""
    if csv_col is None:
        return None
    try:
        val = row.get(csv_col)
        if pd.isna(val):
            return None
        return val
    except Exception:
        return None


# ── Record builders ──────────────────────────────────────────────────────────


def _build_school_record(row):
    return {
        db_col: _safe_str(_get(row, csv_col), 255) if db_col != "school_id"
                else str(row["school_id"])
        for db_col, csv_col in SCHOOL_MAP.items()
    }


def _build_yearly_record(row):
    return {
        "school_id":       str(row["school_id"]),
        "academic_year":   _safe_str(_get(row, YEARLY_MAP["academic_year"]), 20),
        "total_enrolment": _safe_int(_get(row, YEARLY_MAP["total_enrolment"])),
        "attendance_rate": _safe_float(_get(row, YEARLY_MAP["attendance_rate"])),
    }


def _build_infra_record(row):
    rec = {}

    # Direct-mapped columns
    for db_col, csv_col in INFRA_DIRECT_MAP.items():
        if db_col == "school_id":
            rec[db_col] = str(row["school_id"])
        elif db_col == "academic_year":
            rec[db_col] = _safe_str(_get(row, csv_col), 20)
        elif db_col == "building_condition":
            rec[db_col] = _safe_str(_get(row, csv_col), 50)
        else:
            rec[db_col] = _safe_int(_get(row, csv_col))

    # Boolean flags
    for db_col, csv_col in INFRA_BOOL_MAP.items():
        rec[db_col] = _flag_to_bool(_get(row, csv_col))

    # Computed: classroom_condition_score
    major = _safe_int(_get(row, "classrooms_needs_major_repair")) or 0
    minor = _safe_int(_get(row, "classrooms_needs_minor_repair")) or 0
    major_raw = _get(row, "classrooms_needs_major_repair")
    minor_raw = _get(row, "classrooms_needs_minor_repair")
    if major_raw is None and minor_raw is None:
        rec["classroom_condition_score"] = None
    else:
        rec["classroom_condition_score"] = (major * 2) + (minor * 1)

    # Computed: cwsn_toilet_available
    cwsn_b = _safe_int(_get(row, "func_boys_cwsn_friendly"))
    cwsn_g = _safe_int(_get(row, "func_girls_cwsn_friendly"))
    if cwsn_b is None and cwsn_g is None:
        rec["cwsn_toilet_available"] = None
    else:
        rec["cwsn_toilet_available"] = (cwsn_b == 1) or (cwsn_g == 1)

    # Columns with no current source
    rec["required_class_rooms"] = None
    rec["last_major_repair_year"] = None

    return rec


def _build_teacher_record(row):
    return {
        "school_id":        str(row["school_id"]),
        "academic_year":    _safe_str(_get(row, TEACHER_MAP["academic_year"]), 20),
        "total_teachers":   _safe_int(_get(row, TEACHER_MAP["total_teachers"])),
        "required_teachers": None,
    }


# ── Batch inserter ───────────────────────────────────────────────────────────


def _batch_insert(conn, table_name, records):
    if not records:
        return 0
    cols = list(records[0].keys())
    placeholders = ", ".join(f":{c}" for c in cols)
    col_list = ", ".join(cols)
    sql = text(f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})")

    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        conn.execute(sql, batch)
        total += len(batch)
    return total


# ── Main loader ──────────────────────────────────────────────────────────────


def load():
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not found in .env")
        sys.exit(1)

    engine = create_engine(DATABASE_URL, echo=False)

    # ── Read CSV ─────────────────────────────────────────────────────────
    print(f"Reading CSV: {CSV_PATH}")
    t0 = time.time()
    df = pd.read_csv(CSV_PATH, low_memory=False)
    print(f"  Loaded {len(df):,} rows × {len(df.columns)} columns "
          f"in {time.time() - t0:.1f}s\n")

    # ── Build records ────────────────────────────────────────────────────
    # Schools — one row per school (latest year as canonical profile)
    df_sorted = df.sort_values("year", ascending=False)
    school_latest = df_sorted.drop_duplicates(subset="school_id", keep="first")
    schools_records = [_build_school_record(row) for _, row in school_latest.iterrows()]

    # Fact tables — one row per school-year
    yearly_records = []
    infra_records = []
    teacher_records = []

    for _, row in df.iterrows():
        yearly_records.append(_build_yearly_record(row))
        infra_records.append(_build_infra_record(row))
        teacher_records.append(_build_teacher_record(row))

    # ── Insert into database (single transaction) ────────────────────────
    print("Clearing existing data (idempotent reset)...")
    with engine.begin() as conn:
        for tbl in ["teacher_metrics", "infrastructure_details",
                     "yearly_metrics", "schools"]:
            conn.execute(text(f"DELETE FROM {tbl}"))
            print(f"  [OK] Cleared '{tbl}'")
    print()

    print("Inserting data...\n")
    t1 = time.time()

    with engine.begin() as conn:
        n = _batch_insert(conn, "schools", schools_records)
        print(f"  [OK] schools                → {n:>7,} rows")

        n = _batch_insert(conn, "yearly_metrics", yearly_records)
        print(f"  [OK] yearly_metrics         → {n:>7,} rows")

        n = _batch_insert(conn, "infrastructure_details", infra_records)
        print(f"  [OK] infrastructure_details → {n:>7,} rows")

        n = _batch_insert(conn, "teacher_metrics", teacher_records)
        print(f"  [OK] teacher_metrics        → {n:>7,} rows")

    elapsed = time.time() - t1
    print(f"\nAll inserts completed in {elapsed:.1f}s")

    # ── Summary ──────────────────────────────────────────────────────────
    print("\n" + "=" * 56)
    print("  Load Summary")
    print("=" * 56)
    print(f"  Total schools (distinct) : {len(schools_records):,}")
    print(f"  Total school-year rows   : {len(yearly_records):,}")
    print(f"  Academic years           : {sorted(df['year'].unique().tolist())}")
    print("=" * 56)
    print("\nPhase 1.2 complete — data loaded successfully.")


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 56)
    print("  School AI BAV — Flexible Schema-Mapped Data Loader")
    print("=" * 56 + "\n")
    load()
