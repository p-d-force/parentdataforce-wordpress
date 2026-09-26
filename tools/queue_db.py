#!/usr/bin/env python3
"""SQLite-backed reader-request queue for the Massachusetts Student
Settlement Records Project (the "Requested next" section of WP page 41).

Own DB file (settlements_queue.sqlite) so queue history can be committed and
refreshed independently of the tracker DB (settlements.sqlite). Submissions
flow: page form -> WP mu-plugin (pdforce-queue-mu.php, private
pdforce_queue_note posts) -> `settlements_db.py queue-ingest` (upserts here,
then auto-merges against the tracker) -> `build_settlements_page.py` renders.

Usage (run from tools/):
  python queue_db.py init
  python queue_db.py seed       # idempotent: INSERT OR IGNORE, counts unchanged
"""
import argparse
import datetime
import os
import sqlite3
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "settlements_queue.sqlite")

QUEUE_DDL = """
CREATE TABLE IF NOT EXISTS queue (
    id INTEGER PRIMARY KEY,
    district TEXT NOT NULL UNIQUE,
    jurisdiction TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    requested_count INTEGER NOT NULL DEFAULT 1,
    first_requested TEXT NOT NULL,     -- ISO date
    last_requested TEXT NOT NULL,      -- ISO date
    source TEXT NOT NULL DEFAULT 'reader',  -- 'reader' | 'seed'
    queued INTEGER NOT NULL DEFAULT 1, -- 0 = served/removed, retained for counts
    created_at TEXT NOT NULL
);
"""
QUEUE_META_DDL = """
CREATE TABLE IF NOT EXISTS queue_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""
SCHEMA = QUEUE_DDL + QUEUE_META_DDL

# The six districts the pre-queue era collected from readers (hard-coded
# REQUESTED_NEXT on the page before this DB existed).
SEED_DATE = "2026-09-24"
SEED_NOTE = "Suggested by a reader before the queue form existed."
SEED_DISTRICTS = (
    ("Auburn Public Schools", "Auburn"),
    ("Chelmsford Public Schools", "Chelmsford"),
    ("Haverhill Public Schools", "Haverhill"),
    ("Lawrence Public Schools", "Lawrence"),
    ("Newton Public Schools", "Newton"),
    ("North Andover Public Schools", "North Andover"),
)

META_DEFAULTS = {
    "name": "Massachusetts Student Settlement Records Project — request queue",
    "snapshot_date": SEED_DATE,
    "seeded_at": SEED_DATE,
}


def open_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def upsert(conn, district, jurisdiction, note="", source="reader", date=None):
    """Insert a queue row, or bump requested_count if the district is already
    queued (case-insensitive match). Commits nothing; caller commits.
    Returns 'inserted' or 'bumped'."""
    district = str(district).strip()
    jurisdiction = str(jurisdiction).strip()
    note = str(note).strip()
    date = date or datetime.date.today().isoformat()
    if not district:
        raise ValueError("district name is required")
    if source not in ("reader", "seed"):
        raise ValueError(f"invalid source {source!r}; expected 'reader' or 'seed'")
    row = conn.execute(
        "SELECT id, note FROM queue WHERE lower(district) = lower(?)",
        (district,)).fetchone()
    if row:
        new_note = note or row["note"]
        conn.execute(
            "UPDATE queue SET requested_count = requested_count + 1, "
            "last_requested = max(last_requested, ?), note = ? WHERE id = ?",
            (date, new_note, row["id"]))
        return "bumped"
    conn.execute(
        "INSERT INTO queue (district, jurisdiction, note, requested_count, "
        "first_requested, last_requested, source, queued, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (district, jurisdiction, note, 1, date, date, source, 1,
         datetime.datetime.now().isoformat(timespec="seconds")))
    return "inserted"


def cmd_init(args):
    conn = open_db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print("schema ready")


def cmd_seed(args):
    conn = open_db()
    seeded = skipped = 0
    for district, jurisdiction in SEED_DISTRICTS:
        cur = conn.execute(
            "INSERT OR IGNORE INTO queue (district, jurisdiction, note, "
            "requested_count, first_requested, last_requested, source, queued, "
            "created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (district, jurisdiction, SEED_NOTE, 1, SEED_DATE, SEED_DATE,
             "seed", 1, SEED_DATE + "T00:00:00"))
        if cur.rowcount:
            seeded += 1
        else:
            skipped += 1
    for key, value in META_DEFAULTS.items():
        conn.execute("INSERT OR REPLACE INTO queue_meta (key, value) VALUES (?,?)",
                     (key, value))
    conn.commit()
    conn.close()
    print(f"seeded {seeded}, skipped {skipped} (exists)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init").set_defaults(func=cmd_init)
    sub.add_parser("seed").set_defaults(func=cmd_seed)
    args = ap.parse_args()
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    args.func(args)


if __name__ == "__main__":
    main()
