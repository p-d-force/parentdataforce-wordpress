#!/usr/bin/env python3
"""SQLite-backed source of truth for the Massachusetts Student Settlement
Records Project tracker (WordPress page 41).

Replaces hand-edited dated JSON snapshots on Drive: the committed
settlements.sqlite is authoritative, and export-json regenerates a
snapshot-shaped JSON handoff mirror.

Usage:
  python settlements_db.py init
  python settlements_db.py import-json <snapshot.json>
  python settlements_db.py add-district --name N --jurisdiction J --submitted YYYY-MM-DD [--note "…"]
  python settlements_db.py ack --name SUBSTR --date YYYY-MM-DD [--note "…"] [--ref REQNUM]
  python settlements_db.py note --name SUBSTR --text "…"
  python settlements_db.py mark --name SUBSTR --status <enum>
  python settlements_db.py re-send --name SUBSTR
  python settlements_db.py stats
  python settlements_db.py publish [--status draft|publish]
  python settlements_db.py export-json <snapshot.json>
"""
import argparse
import datetime
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wp_api  # noqa: E402
import build_settlements_page as bsp  # noqa: E402

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settlements.sqlite")

SCHEMA = """
CREATE TABLE IF NOT EXISTS districts (
    id INTEGER PRIMARY KEY,
    district TEXT NOT NULL UNIQUE,
    jurisdiction TEXT NOT NULL,
    submitted TEXT NOT NULL,            -- ISO date
    expected_initial_response TEXT,     -- ISO date, may be empty
    status TEXT NOT NULL CHECK (status IN
      ('awaiting_initial_response','acknowledged','records_received_review_pending',
       'partial_production','complete_published','no_responsive_records','appeal_compliance')),
    acknowledged TEXT,                  -- ISO date or NULL
    records_received INTEGER NOT NULL DEFAULT 0,
    public_note TEXT NOT NULL DEFAULT '',
    records_url TEXT,
    last_public_update TEXT NOT NULL,
    excluded INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS project_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

STATUS_VALUES = (
    "awaiting_initial_response", "acknowledged", "records_received_review_pending",
    "partial_production", "complete_published", "no_responsive_records",
    "appeal_compliance",
)

BOUNCE_FRAG = ("The initial send bounced on an incorrect address and was re-sent "
               "to the district's published records inbox.")
BOUNCE_CLEAR = ("Re-sent to the district's published records inbox after an "
                "initial delivery failure.")


def open_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def add_business_days(start, n):
    d = datetime.date.fromisoformat(start)
    added = 0
    while added < n:
        d += datetime.timedelta(days=1)
        if d.weekday() < 5:
            added += 1
    return d.isoformat()


def import_json(args):
    with open(args.path, encoding="utf-8-sig") as f:
        snap = json.load(f)
    conn = open_db()
    seeded = skipped = 0
    for row in snap.get("districts", []):
        if "Worcester" in row["district"]:
            continue
        cur = conn.execute(
            "INSERT OR IGNORE INTO districts (district, jurisdiction, submitted, "
            "expected_initial_response, status, acknowledged, records_received, "
            "public_note, records_url, last_public_update) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (row["district"], row["jurisdiction"], row["submitted"],
             row.get("expected_initial_response"), row["status"],
             row.get("acknowledged"), 1 if row.get("records_received") else 0,
             row.get("public_note") or "", row.get("records_url"),
             row.get("last_public_update") or row["submitted"]))
        if cur.rowcount:
            seeded += 1
        else:
            skipped += 1
    for key in ("name", "snapshot_date", "owner", "contact_email",
                "request_window_start", "request_set_id"):
        if snap.get("project", {}).get(key) is not None:
            conn.execute("INSERT OR REPLACE INTO project_meta (key, value) VALUES (?,?)",
                         (key, str(snap["project"][key])))
    conn.commit()
    conn.close()
    print(f"seeded {seeded}, skipped {skipped} (exists)")


def _get_row(conn, name):
    rows = conn.execute(
        "SELECT * FROM districts WHERE lower(district) LIKE ? ORDER BY district",
        (f"%{name.lower()}%",)).fetchall()
    if not rows:
        sys.exit(f"no district matches {name!r}")
    if len(rows) > 1:
        cands = ", ".join(r["district"] for r in rows)
        sys.exit(f"ambiguous match for {name!r}: {cands}")
    return rows[0]


def _stamp(conn, row, fields):
    conn.execute(f"UPDATE districts SET {', '.join(k + '=?' for k in fields)} WHERE id=?",
                 list(fields.values()) + [row["id"]])
    conn.commit()
    conn.close()


def cmd_add_district(args):
    conn = open_db()
    expected = add_business_days(args.submitted, 10)
    conn.execute(
        "INSERT INTO districts (district, jurisdiction, submitted, "
        "expected_initial_response, status, last_public_update, public_note) "
        "VALUES (?,?,?,?,?,?,?)",
        (args.name, args.jurisdiction, args.submitted, expected,
         "awaiting_initial_response", args.submitted, args.note or ""))
    conn.commit()
    conn.close()
    print(f"added {args.name}: submitted {args.submitted}, expected {expected}")


def cmd_ack(args):
    conn = open_db()
    row = _get_row(conn, args.name)
    fields = {"status": "acknowledged", "acknowledged": args.date,
              "last_public_update": args.date}
    if args.note is not None:
        note = args.note
    elif args.ref:
        note = row["public_note"]
        frag = f" (Request #{args.ref})"
        if frag not in note:
            note += frag
    else:
        note = row["public_note"]
    fields["public_note"] = note
    _stamp(conn, row, fields)
    print(f"acknowledged {row['district']} on {args.date}")


def cmd_note(args):
    conn = open_db()
    row = _get_row(conn, args.name)
    today = datetime.date.today().isoformat()
    _stamp(conn, row, {"public_note": args.text, "last_public_update": today})
    print(f"note set on {row['district']}")


def cmd_mark(args):
    if args.status not in STATUS_VALUES:
        sys.exit(f"invalid status {args.status!r}; valid: {', '.join(STATUS_VALUES)}")
    conn = open_db()
    row = _get_row(conn, args.name)
    today = datetime.date.today().isoformat()
    _stamp(conn, row, {"status": args.status, "last_public_update": today})
    print(f"{row['district']} -> {args.status}")


def cmd_resend(args):
    conn = open_db()
    row = _get_row(conn, args.name)
    note = row["public_note"].replace(BOUNCE_FRAG, BOUNCE_CLEAR)
    _stamp(conn, row, {"public_note": note})
    print(f"re-send note cleared on {row['district']}")


def cmd_stats(args):
    conn = open_db()
    total = conn.execute("SELECT COUNT(*) c FROM districts WHERE excluded=0").fetchone()["c"]
    ack = conn.execute("SELECT COUNT(*) c FROM districts WHERE excluded=0 AND status='acknowledged'").fetchone()["c"]
    awaiting = conn.execute("SELECT COUNT(*) c FROM districts WHERE excluded=0 AND status='awaiting_initial_response'").fetchone()["c"]
    prod = conn.execute("SELECT COUNT(*) c FROM districts WHERE excluded=0 AND records_url IS NOT NULL").fetchone()["c"]
    conn.close()
    print(f"total={total}, acknowledged={ack}, awaiting={awaiting}, productions={prod}")


def _project_and_rows(conn):
    meta = dict(conn.execute("SELECT key, value FROM project_meta").fetchall())
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM districts WHERE excluded=0 ORDER BY district").fetchall()]
    if not rows:
        sys.exit("no districts in DB — run init/import-json first")
    project = {
        "name": meta.get("name", "Massachusetts Student Settlement Records Project"),
        "owner": meta.get("owner", "Parent Data Force"),
        "contact_email": meta.get("contact_email", bsp.CONTACT),
        "request_window_start": meta.get("request_window_start", "2021-09-18"),
        "request_set_id": meta.get("request_set_id", ""),
        "snapshot_date": max(r["last_public_update"] for r in rows),
        "district_count": len(rows),
        "acknowledged_count": sum(1 for r in rows if r["status"] == "acknowledged"),
        "production_count": sum(1 for r in rows if r.get("records_url")),
    }
    return project, rows


def _publish(project, rows, status):
    content = bsp.build_blocks(project, rows)
    c = wp_api.client()
    existing = c.call(
        "GET",
        f"/wp/v2/pages?slug={bsp.SLUG}&status=publish,draft,pending,private&per_page=10",
        quiet=True,
    )
    payload = {"title": bsp.TITLE, "content": content, "status": status,
               "template": bsp.PAGE_TEMPLATE}
    if existing:
        page = existing[0]
        result = c.call("POST", f"/wp/v2/pages/{page['id']}", payload, quiet=True)
        action = "updated"
    else:
        payload["slug"] = bsp.SLUG
        result = c.call("POST", "/wp/v2/pages", payload, quiet=True)
        action = "created"
    print(json.dumps({"action": action, "id": result["id"], "link": result["link"],
                      "rows": len(rows)}, ensure_ascii=False))


def cmd_publish(args):
    conn = open_db()
    project, rows = _project_and_rows(conn)
    conn.close()
    # build_blocks expects the snapshot row shape (booleans, no excluded col).
    for r in rows:
        r["records_received"] = bool(r.pop("records_received"))
    _publish(project, rows, args.status)


def cmd_export_json(args):
    conn = open_db()
    project, rows = _project_and_rows(conn)
    conn.close()
    snap = {"project": project, "districts": [
        {
            "district": r["district"],
            "jurisdiction": r["jurisdiction"],
            "submitted": r["submitted"],
            "expected_initial_response": r["expected_initial_response"],
            "status": r["status"],
            "status_label": {"awaiting_initial_response": "Active / awaiting initial response",
                             "acknowledged": "Acknowledged"}.get(r["status"], r["status"]),
            "acknowledged": r["acknowledged"],
            "records_received": bool(r["records_received"]),
            "public_note": r["public_note"],
            "records_url": r["records_url"],
            "last_public_update": r["last_public_update"],
        } for r in rows]}
    with open(args.path, "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"exported {len(rows)} rows -> {args.path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init").set_defaults(func=lambda a: (open_db().executescript(SCHEMA), print("schema ready")))
    p = sub.add_parser("import-json"); p.add_argument("path"); p.set_defaults(func=import_json)
    p = sub.add_parser("add-district")
    p.add_argument("--name", required=True); p.add_argument("--jurisdiction", required=True)
    p.add_argument("--submitted", required=True); p.add_argument("--note")
    p.set_defaults(func=cmd_add_district)
    p = sub.add_parser("ack")
    p.add_argument("--name", required=True); p.add_argument("--date", required=True)
    p.add_argument("--note"); p.add_argument("--ref")
    p.set_defaults(func=cmd_ack)
    p = sub.add_parser("note")
    p.add_argument("--name", required=True); p.add_argument("--text", required=True)
    p.set_defaults(func=cmd_note)
    p = sub.add_parser("mark")
    p.add_argument("--name", required=True); p.add_argument("--status", required=True)
    p.set_defaults(func=cmd_mark)
    p = sub.add_parser("re-send")
    p.add_argument("--name", required=True)
    p.set_defaults(func=cmd_resend)
    sub.add_parser("stats").set_defaults(func=cmd_stats)
    p = sub.add_parser("publish")
    p.add_argument("--status", choices=("draft", "publish"), default="publish")
    p.set_defaults(func=cmd_publish)
    p = sub.add_parser("export-json")
    p.add_argument("path"); p.set_defaults(func=cmd_export_json)
    args = ap.parse_args()
    if args.cmd != "init":
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    args.func(args)


if __name__ == "__main__":
    main()
