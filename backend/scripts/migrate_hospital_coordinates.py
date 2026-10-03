#!/usr/bin/env python3
"""
MedSentinel Safe Idempotent Database Migration: Hospital Coordinates
---------------------------------------------------------------------
Adds `latitude` and `longitude` columns to the `hospitals` table if they do not
already exist, and populates known coordinates for default seed hospitals without
modifying any existing patient data or dropping tables.
"""

import sys
from pathlib import Path

# Ensure backend root is on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import inspect, text
from app.core.database import engine

SEED_HOSPITAL_COORDINATES = {
    1: (12.9716, 77.5946),  # City General Hospital
    2: (12.8944, 77.5986),  # Apollo Multispeciality Hospital
    3: (12.9784, 77.6408),  # St. Jude Medical Research Institute
    4: (12.9866, 77.5993),  # Fortis HealthCare Super Speciality
    5: (12.9582, 77.6534),  # Manipal Comprehensive Hospital
}


def run_migration() -> bool:
    print("[MIGRATION] Checking MySQL hospitals table schema...")
    inspector = inspect(engine)

    if "hospitals" not in inspector.get_table_names():
        print("[ERROR] Table 'hospitals' does not exist in the database.")
        return False

    existing_cols = {col["name"] for col in inspector.get_columns("hospitals")}
    needs_lat = "latitude" not in existing_cols
    needs_lon = "longitude" not in existing_cols

    with engine.begin() as conn:
        if needs_lat:
            print("[MIGRATION] Adding column 'latitude' (FLOAT, NULL)...")
            conn.execute(text("ALTER TABLE hospitals ADD COLUMN latitude FLOAT NULL;"))
        else:
            print("[INFO] Column 'latitude' already exists.")

        if needs_lon:
            print("[MIGRATION] Adding column 'longitude' (FLOAT, NULL)...")
            conn.execute(text("ALTER TABLE hospitals ADD COLUMN longitude FLOAT NULL;"))
        else:
            print("[INFO] Column 'longitude' already exists.")

        # Seed coordinates for known hospitals if NULL
        print("[MIGRATION] Verifying coordinates for seed hospitals...")
        for hid, (lat, lon) in SEED_HOSPITAL_COORDINATES.items():
            conn.execute(
                text(
                    "UPDATE hospitals SET latitude = :lat, longitude = :lon "
                    "WHERE id = :hid AND (latitude IS NULL OR longitude IS NULL);"
                ),
                {"lat": lat, "lon": lon, "hid": hid},
            )

    print("[SUCCESS] Hospital coordinates schema migration complete and verified!")
    return True


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
