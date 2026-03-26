"""
Script to import bank branch data from the CSV file into SQLite.

Run this once before starting the server:
    python scripts/import_data.py

The CSV comes from: https://github.com/Amanskywalker/indian_banks
It has these columns: ifsc, bank_id, branch, address, city, district, state, bank_name
"""

import csv
import os
import sys
import time

# add parent dir to path so we can import the app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal, Base
from app.models import Bank, Branch


CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "bank_branches.csv",
)


def import_data():
    """Read the CSV and populate the banks + branches tables."""

    if not os.path.exists(CSV_PATH):
        print(f"ERROR: CSV file not found at {CSV_PATH}")
        print("Make sure you've placed bank_branches.csv in the data/ directory.")
        sys.exit(1)

    # create tables if they don't exist
    Base.metadata.drop_all(bind=engine)  # start fresh
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        print("Reading CSV file...")
        start = time.time()

        # first pass: collect unique banks
        banks_seen = {}  # bank_id -> bank_name
        rows = []

        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # skip empty rows (there are some in the csv)
                if not row.get("ifsc") or not row["ifsc"].strip():
                    continue

                bank_id = int(row["bank_id"])
                bank_name = row["bank_name"].strip()

                if bank_id not in banks_seen:
                    banks_seen[bank_id] = bank_name

                rows.append(row)

        print(f"Found {len(banks_seen)} unique banks and {len(rows)} branches")

        # insert banks
        print("Inserting banks...")
        bank_objects = [
            Bank(id=bid, name=bname)
            for bid, bname in sorted(banks_seen.items())
        ]
        db.bulk_save_objects(bank_objects)
        db.commit()
        print(f"  -> {len(bank_objects)} banks inserted")

        # insert branches in chunks (sqlite doesn't love huge single inserts)
        print("Inserting branches (this might take a moment)...")
        chunk_size = 5000
        total_inserted = 0

        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            branch_objects = []

            for row in chunk:
                branch_objects.append(
                    Branch(
                        ifsc=row["ifsc"].strip(),
                        bank_id=int(row["bank_id"]),
                        branch=row.get("branch", "").strip() or None,
                        address=row.get("address", "").strip() or None,
                        city=row.get("city", "").strip() or None,
                        district=row.get("district", "").strip() or None,
                        state=row.get("state", "").strip() or None,
                    )
                )

            db.bulk_save_objects(branch_objects)
            db.commit()
            total_inserted += len(branch_objects)

            # progress indicator
            pct = min(100, int((total_inserted / len(rows)) * 100))
            print(f"  -> {total_inserted}/{len(rows)} branches ({pct}%)")

        elapsed = time.time() - start
        print(f"\nDone! Imported everything in {elapsed:.1f} seconds.")
        print(f"Database saved to: {os.path.join(os.path.dirname(CSV_PATH), '..', 'bank_data.db')}")

    except Exception as e:
        db.rollback()
        print(f"ERROR during import: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_data()
