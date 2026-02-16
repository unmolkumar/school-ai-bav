"""
bootstrap_schema.py

Idempotent schema bootstrap for the School AI BAV online MySQL database.

Phase 1.1 — Expanded infrastructure_details to align with Problem Statement 5
(AI Solutions for Scalable and Sustainable School Infrastructure Planning).

Safe to run multiple times:
  - Other tables use CREATE TABLE IF NOT EXISTS.
  - infrastructure_details is dropped and recreated to ensure the latest schema.
"""

import os
import sys

from dotenv import load_dotenv
from sqlalchemy import (
    Boolean,
    Column,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    inspect,
    text,
)

# ── Load environment ─────────────────────────────────────────────────────────
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in .env")
    sys.exit(1)

# ── Engine & metadata ────────────────────────────────────────────────────────
engine = create_engine(DATABASE_URL, echo=False)
metadata = MetaData()

# ── Table definitions ────────────────────────────────────────────────────────

schools = Table(
    "schools",
    metadata,
    Column("school_id", String(50), primary_key=True),
    Column("school_name", String(255)),
    Column("district", String(100)),
    Column("block", String(100)),
    Column("management_type", String(100)),
    Column("school_category", String(100)),
    Column("latitude", Float),
    Column("longitude", Float),
)

yearly_metrics = Table(
    "yearly_metrics",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("school_id", String(50)),
    Column("academic_year", String(20)),
    Column("total_enrolment", Integer),
    Column("attendance_rate", Float),
)

infrastructure_details = Table(
    "infrastructure_details",
    metadata,
    # ── Identity
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("school_id", String(50)),
    Column("academic_year", String(20)),
    # ── Classroom Capacity
    Column("total_class_rooms", Integer),
    Column("usable_class_rooms", Integer),
    Column("required_class_rooms", Integer),
    Column("classroom_condition_score", Integer),
    # ── Basic Facilities
    Column("drinking_water_available", Boolean),
    Column("electricity_available", Boolean),
    Column("internet_available", Boolean),
    # ── Sanitation & Gender Compliance
    Column("separate_girls_toilet", Boolean),
    Column("cwsn_toilet_available", Boolean),
    # ── Accessibility
    Column("ramp_available", Boolean),
    Column("resource_room_available", Boolean),
    # ── Structural Condition
    Column("building_condition", String(50)),
    Column("last_major_repair_year", Integer),
)

teacher_metrics = Table(
    "teacher_metrics",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("school_id", String(50)),
    Column("academic_year", String(20)),
    Column("total_teachers", Integer),
    Column("required_teachers", Integer),
)

# ── Create tables & confirm ──────────────────────────────────────────────────

def bootstrap():
    """Drop and recreate infrastructure_details; create other tables if needed."""

    print("Step 1/3 — Dropping old infrastructure_details (if exists)...")
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS infrastructure_details"))
    print("  [OK] Old infrastructure_details removed.\n")

    print("Step 2/3 — Creating / verifying all tables...")
    metadata.create_all(engine)

    print("Step 3/3 — Confirming tables...\n")
    inspector = inspect(engine)
    existing = inspector.get_table_names()

    expected = ["schools", "yearly_metrics", "infrastructure_details", "teacher_metrics"]

    for table_name in expected:
        if table_name in existing:
            print(f"  [OK] Table '{table_name}' is ready.")
        else:
            print(f"  [!!] Table '{table_name}' was NOT created — check logs.")

    print("\nBootstrap complete.")


if __name__ == "__main__":
    print("=" * 56)
    print("  School AI BAV — Database Schema Bootstrap (v1.1)")
    print("=" * 56 + "\n")
    bootstrap()
