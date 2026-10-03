#!/usr/bin/env python3
"""
MedSentinel Hospital CSV Data Import System
--------------------------------------------
Imports hospital records from a CSV file into the MySQL `hospitals` table.
Features:
 - File & schema validation
 - Field cleaning & whitespace normalization
 - Safe type conversion & range validation (ratings, distance, costs)
 - Batch duplicate detection (name + location normalization)
 - Transaction safety & rollback on failure
 - Detailed validation logging & summary reporting
"""

import sys
import os
import csv
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Set

# Ensure backend directory is in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Ensure root directory is also reachable for .env resolution
ROOT_DIR = BACKEND_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.database import SessionLocal, engine, Base
from app.models.hospital import Hospital


def normalize_key(name: str, location: Optional[str] = None) -> str:
    """Generate a normalized key for duplicate detection."""
    clean_name = (name or "").strip().lower()
    clean_loc = (location or "").strip().lower()
    return f"{clean_name}:::{clean_loc}"


def parse_boolean(val: Any) -> bool:
    """Parse various representations of booleans."""
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    return s in ("1", "true", "yes", "t", "y", "available")


def clean_string(val: Any, default: Optional[str] = None) -> Optional[str]:
    """Clean whitespace and treat empty strings as default/None."""
    if val is None:
        return default
    s = str(val).strip()
    return s if s else default


def validate_and_clean_row(
    row_num: int,
    raw_row: Dict[str, str]
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Validates and cleans a single CSV record.
    Returns: (cleaned_dict, error_message_if_any)
    """
    # Normalize dictionary keys (lowercase, stripped)
    row = {k.strip().lower(): v for k, v in raw_row.items() if k}

    # 1. Hospital Name (Required)
    name = clean_string(row.get("name") or row.get("hospital_name") or row.get("hospital"))
    if not name:
        return None, f"Row {row_num}: Missing required hospital name."
    if len(name) > 200:
        return None, f"Row {row_num}: Hospital name exceeds 200 characters ({len(name)} chars)."

    # 2. Location (City, State, Address handling)
    location = clean_string(row.get("location"))
    if not location:
        city = clean_string(row.get("city"))
        state = clean_string(row.get("state"))
        address = clean_string(row.get("address"))
        loc_parts = [p for p in (address, city, state) if p]
        location = ", ".join(loc_parts) if loc_parts else None

    if location and len(location) > 200:
        location = location[:200]

    # 3. Specialization / Specialty
    specialization = clean_string(
        row.get("specialization") or row.get("specialty") or row.get("specialities")
    )
    if specialization and len(specialization) > 200:
        specialization = specialization[:200]

    # 4. Rating (0.0 to 5.0)
    raw_rating = clean_string(row.get("rating"))
    rating = 0.0
    if raw_rating is not None:
        try:
            rating = float(raw_rating)
            if rating < 0.0 or rating > 5.0:
                return None, f"Row {row_num}: Rating {rating} out of valid range (0.0 - 5.0)."
        except ValueError:
            return None, f"Row {row_num}: Invalid rating format '{raw_rating}'."

    # 5. Distance (>= 0.0 km)
    raw_distance = clean_string(row.get("distance"))
    distance = 0.0
    if raw_distance is not None:
        try:
            # Handle possible 'km' suffix e.g. "3.5 km"
            clean_dist = raw_distance.lower().replace("km", "").strip()
            distance = float(clean_dist)
            if distance < 0.0:
                return None, f"Row {row_num}: Negative distance value '{raw_distance}'."
        except ValueError:
            return None, f"Row {row_num}: Invalid distance format '{raw_distance}'."

    # 6. Cost Range / Consultation Cost
    cost_range = clean_string(row.get("cost_range"))
    if not cost_range:
        consult_cost = clean_string(row.get("consultation_cost") or row.get("cost"))
        if consult_cost:
            cost_range = f"₹{consult_cost}" if not consult_cost.startswith("₹") else consult_cost

    if cost_range and len(cost_range) > 100:
        cost_range = cost_range[:100]

    # 7. Bed Capacity -> incorporate into facilities if present
    bed_capacity = clean_string(row.get("bed_capacity") or row.get("beds"))
    facilities = clean_string(row.get("facilities"))

    if bed_capacity:
        try:
            beds_int = int(bed_capacity)
            if beds_int < 0:
                return None, f"Row {row_num}: Bed capacity cannot be negative ({bed_capacity})."
            bed_str = f"{beds_int} Beds"
            if facilities:
                if "bed" not in facilities.lower():
                    facilities = f"{bed_str}, {facilities}"
            else:
                facilities = bed_str
        except ValueError:
            return None, f"Row {row_num}: Invalid bed capacity '{bed_capacity}'."

    # 8. Schemes & Insurances
    schemes = clean_string(row.get("schemes") or row.get("government_schemes"))
    insurance_accepted = clean_string(
        row.get("insurance_accepted") or row.get("insurance_supported") or row.get("insurance")
    )

    # 9. Availability
    raw_available = row.get("is_available") or row.get("available")
    is_available = parse_boolean(raw_available) if raw_available is not None else True

    # 10. Contact Info
    phone = clean_string(row.get("phone") or row.get("contact"))
    if phone and len(phone) > 50:
        phone = phone[:50]

    email = clean_string(row.get("email"))
    if email and len(email) > 100:
        email = email[:100]

    description = clean_string(row.get("description"))
    image_url = clean_string(row.get("image_url"))
    # 11. Geographic Coordinates (Optional)
    raw_lat = clean_string(row.get("latitude") or row.get("lat"))
    raw_lon = clean_string(row.get("longitude") or row.get("lon") or row.get("lng"))
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    if raw_lat is not None:
        try:
            latitude = float(raw_lat)
            if not (-90.0 <= latitude <= 90.0):
                return None, f"Row {row_num}: Latitude {latitude} out of valid range (-90 to 90)."
        except ValueError:
            return None, f"Row {row_num}: Invalid latitude format '{raw_lat}'."
    if raw_lon is not None:
        try:
            longitude = float(raw_lon)
            if not (-180.0 <= longitude <= 180.0):
                return None, f"Row {row_num}: Longitude {longitude} out of valid range (-180 to 180)."
        except ValueError:
            return None, f"Row {row_num}: Invalid longitude format '{raw_lon}'."

    cleaned = {
        "name": name,
        "location": location,
        "specialization": specialization,
        "rating": round(rating, 2),
        "distance": round(distance, 2),
        "cost_range": cost_range,
        "schemes": schemes,
        "insurance_accepted": insurance_accepted,
        "is_available": is_available,
        "image_url": image_url,
        "facilities": facilities,
        "description": description,
        "phone": phone,
        "email": email,
        "latitude": latitude,
        "longitude": longitude,
    }

    return cleaned, None


def load_existing_hospital_keys(db) -> Set[str]:
    """Fetch all existing hospital duplicate identification keys in one fast query."""
    existing_records = db.query(Hospital.name, Hospital.location).all()
    keys = set()
    for name, location in existing_records:
        keys.add(normalize_key(name, location))
        # Also store clean name alone for fallback matching
        if name:
            keys.add(name.strip().lower())
    return keys


def import_hospitals_from_csv(
    file_path: str,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Main import pipeline:
      CSV -> Validation -> Cleaning -> Batch Duplicate Check -> SQLAlchemy -> MySQL
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found at: {path.resolve()}")

    if path.stat().st_size == 0:
        raise ValueError(f"CSV file is empty: {path.resolve()}")

    stats = {
        "total_rows": 0,
        "valid_rows": 0,
        "invalid_rows": 0,
        "new_hospitals": 0,
        "duplicates_skipped": 0,
        "import_errors": 0,
    }

    validation_errors: List[str] = []
    hospitals_to_insert: List[Dict[str, Any]] = []

    print(f"\n[1/4] Reading & Validating CSV: {path.resolve()}")

    with open(path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV has no headers or is improperly formatted.")

        # Check that a name column exists
        header_keys = [h.strip().lower() for h in reader.fieldnames if h]
        has_name = any(k in header_keys for k in ("name", "hospital_name", "hospital"))
        if not has_name:
            raise ValueError(
                f"CSV headers missing required hospital name column. Found headers: {reader.fieldnames}"
            )

        row_num = 1 # Header is row 1
        for raw_row in reader:
            row_num += 1
            # Skip empty lines
            if not any(v.strip() for v in raw_row.values() if v):
                continue

            stats["total_rows"] += 1
            cleaned_row, err = validate_and_clean_row(row_num, raw_row)

            if err:
                stats["invalid_rows"] += 1
                validation_errors.append(err)
            else:
                stats["valid_rows"] += 1
                hospitals_to_insert.append(cleaned_row)

    print(f"      Parsed {stats['total_rows']} rows: {stats['valid_rows']} valid, {stats['invalid_rows']} invalid.")

    if validation_errors:
        print("\n[!] Validation Notices:")
        for err in validation_errors[:10]:
            print(f"    - {err}")
        if len(validation_errors) > 10:
            print(f"    ... and {len(validation_errors) - 10} more invalid rows.")

    print("\n[2/4] Connecting to Database & Fetching Existing Hospitals...")
    db = SessionLocal()

    try:
        existing_keys = load_existing_hospital_keys(db)
        print(f"      Found {len(existing_keys)} existing entries in database.")

        print("\n[3/4] Duplicate Detection & Preparation...")
        new_records: List[Hospital] = []
        batch_seen_keys: Set[str] = set()

        for data in hospitals_to_insert:
            full_key = normalize_key(data["name"], data["location"])
            name_only_key = data["name"].strip().lower()

            # Check if exists in DB or already queued in current batch
            if full_key in existing_keys or full_key in batch_seen_keys:
                stats["duplicates_skipped"] += 1
                continue

            # If location is provided, also check if same name exists at same location
            if name_only_key in existing_keys and not data.get("location"):
                stats["duplicates_skipped"] += 1
                continue

            batch_seen_keys.add(full_key)
            new_records.append(Hospital(**data))

        stats["new_hospitals"] = len(new_records)
        print(f"      New hospitals to insert: {stats['new_hospitals']}")
        print(f"      Duplicates skipped:      {stats['duplicates_skipped']}")

        print("\n[4/4] Writing to MySQL Database...")
        if dry_run:
            print("      [DRY-RUN] Verification complete. Database write skipped (--dry-run).")
        else:
            if new_records:
                db.bulk_save_objects(new_records)
                db.commit()
                print(f"      Successfully committed {len(new_records)} new hospital records to MySQL.")
            else:
                print("      No new hospital records to insert.")

    except Exception as e:
        db.rollback()
        stats["import_errors"] += 1
        print(f"\n[ERROR] Database transaction failed: {e}")
        raise
    finally:
        db.close()

    # Print Formatted Report
    print("\n" + "=" * 60)
    print("HOSPITAL CSV IMPORT REPORT")
    print("=" * 60)
    print(f"TOTAL ROWS:         {stats['total_rows']}")
    print(f"VALID ROWS:         {stats['valid_rows']}")
    print(f"INVALID ROWS:       {stats['invalid_rows']}")
    print(f"NEW HOSPITALS:      {stats['new_hospitals']}")
    print(f"DUPLICATES SKIPPED: {stats['duplicates_skipped']}")
    print(f"IMPORT ERRORS:      {stats['import_errors']}")
    print("=" * 60)

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="MedSentinel Hospital CSV Importer - Imports hospitals into MySQL."
    )
    default_csv = BACKEND_DIR / "data" / "hospitals.csv"
    parser.add_argument(
        "--file", "-f",
        type=str,
        default=str(default_csv),
        help=f"Path to hospitals CSV file (default: {default_csv})"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate CSV and detect duplicates without committing to MySQL"
    )

    args = parser.parse_args()

    try:
        import_hospitals_from_csv(args.file, dry_run=args.dry_run)
    except Exception as e:
        print(f"\nImport aborted: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
