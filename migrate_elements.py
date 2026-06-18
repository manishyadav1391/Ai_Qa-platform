"""
Migration script: Add new columns to 'elements' and 'crawl_runs' tables.

Run once:  python migrate_elements.py
"""

import sqlite3

DB_PATH = "qa_platform_v3.db"

ELEMENTS_COLUMNS = [
    ("tag_name",   "TEXT"),
    ("element_id", "TEXT"),
    ("input_type", "TEXT"),
    ("href",       "TEXT"),
    ("visible",    "TEXT DEFAULT 'true'"),
]

CRAWL_RUNS_COLUMNS = [
    ("pages_found",  "INTEGER DEFAULT 0"),
    ("current_url",  "TEXT"),
    ("completed_at", "DATETIME"),
    ("max_pages",    "INTEGER"),
]


def get_existing_columns(cursor, table):
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def add_columns(cursor, table, columns):
    existing = get_existing_columns(cursor, table)
    print(f"\n[{table}] Existing columns: {sorted(existing)}")

    added = 0
    for col_name, col_type in columns:
        if col_name in existing:
            print(f"  OK Column '{col_name}' already exists, skipping.")
            continue

        sql = f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"
        print(f"  +  Adding column '{col_name}' ({col_type})...")
        cursor.execute(sql)
        added += 1

    return added


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    total = 0
    total += add_columns(cursor, "elements", ELEMENTS_COLUMNS)
    total += add_columns(cursor, "crawl_runs", CRAWL_RUNS_COLUMNS)

    conn.commit()
    conn.close()

    if total:
        print(f"\nMigration complete. Added {total} column(s).")
    else:
        print("\nNothing to migrate -- all columns already exist.")


if __name__ == "__main__":
    migrate()
