#!/usr/bin/env python3
"""SQLite-backed source of truth for the Georgia Student Settlement
Records Project tracker (WordPress page on parentdataforce.com).

Replaces hand-edited dated JSON snapshots on Drive: the committed
ga_settlements.sqlite is authoritative, and export-json regenerates a
snapshot-shaped JSON handoff mirror.

Usage:
  python ga_settlements_db.py init [--meta]
  python ga_settlements_db.py migrate
  python ga_settlements_db.py import-json <snapshot.json>
  python ga_settlements_db.py add-district --name N --jurisdiction J --submitted YYYY-MM-DD [--note "…"]
  python ga_settlements_db.py ack --name SUBSTR --date YYYY-MM-DD [--note "…"] [--ref REQNUM]
  python ga_settlements_db.py note --name SUBSTR --text "…"
  python ga_settlements_db.py mark --name SUBSTR --status <enum> [--clear-ack]
  python ga_settlements_db.py add-document --name SUBSTR --kind request|response|appeal (--file PATH | --url URL) [--filename F] [--label L]
  python ga_settlements_db.py re-send --name SUBSTR
  python ga_settlements_db.py stats
  python ga_settlements_db.py publish [--status draft|publish]
  python ga_settlements_db.py export-json <snapshot.json>
"""
import argparse
import datetime
import json
import os
import sqlite3
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wp_api  # noqa: E402
import build_ga_settlements_page as bsp  # noqa: E402
import ga_queue_db  # noqa: E402

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ga_settlements.sqlite")

DISTRICTS_DDL = """
CREATE TABLE IF NOT EXISTS districts (
    id INTEGER PRIMARY KEY,
    district TEXT NOT NULL UNIQUE,
    jurisdiction TEXT NOT NULL,
    submitted TEXT NOT NULL,            -- ISO date
    expected_initial_response TEXT,     -- ISO date, may be empty
    status TEXT NOT NULL CHECK (status IN
      ('awaiting_initial_response','acknowledged','records_received_review_pending',
       'partial_production','complete_published','no_responsive_records','appeal_compliance',
       'routing_portal','response_fee_estimate','appeal_filed')),
    acknowledged TEXT,                  -- ISO date or NULL
    records_received INTEGER NOT NULL DEFAULT 0,
    public_note TEXT NOT NULL DEFAULT '',
    records_url TEXT,
    last_public_update TEXT NOT NULL,
    excluded INTEGER NOT NULL DEFAULT 0,
    fee_estimate TEXT,                  -- public fee estimate, e.g. '$750' (NULL = none)
    appeal_note TEXT,                   -- public SPR-appeal narrative (NULL = none)
    spr_number TEXT                     -- MA-only mirror of settlements_db.py (do NOT ALTER ga_settlements.sqlite yet)
);
"""
DOCUMENTS_DDL = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    district TEXT NOT NULL,             -- districts.district value
    kind TEXT NOT NULL,                 -- 'request' | 'response' | 'appeal' | 'article' (MA schema)
    label TEXT NOT NULL,
    url TEXT NOT NULL,
    UNIQUE(district, kind)
);
"""
SCHEMA = DISTRICTS_DDL + DOCUMENTS_DDL + """
CREATE TABLE IF NOT EXISTS project_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

STATUS_VALUES = (
    "awaiting_initial_response", "acknowledged", "records_received_review_pending",
    "partial_production", "complete_published", "no_responsive_records",
    "appeal_compliance", "routing_portal", "response_fee_estimate", "appeal_filed",
)

STATUS_LABELS = {
    "awaiting_initial_response": "Active / awaiting initial response",
    "acknowledged": "Acknowledged",
    "records_received_review_pending": "Records received / review pending",
    "partial_production": "Partial production",
    "complete_published": "Complete — published",
    "no_responsive_records": "No responsive records",
    "appeal_compliance": "Appeal / compliance",
    "routing_portal": "Routing / portal",
    "response_fee_estimate": "Response / fee estimate",
    "appeal_filed": "Appeal filed",
}

BOUNCE_FRAG = ("The initial send bounced on an incorrect address and was re-sent "
               "to the district's published records inbox.")
BOUNCE_CLEAR = ("Re-sent to the district's published records inbox after an "
                "initial delivery failure.")


def cmd_init(args):
    """One-shot: create schema; with --meta, seed project_meta with the
    Georgia project's launch values so _project_and_rows never falls back
    to missing values."""
    conn = open_db()
    conn.executescript(SCHEMA)
    if args.meta:
        seed = {
            "name": bsp.TITLE,
            "owner": "Parent Data Force",
            "contact_email": bsp.CONTACT,
            "request_window_start": "2026-09-25",
            "request_set_id": "PRRSET-GA-SETTLEMENTS-20260925-01",
        }
        for key, value in seed.items():
            conn.execute("INSERT OR REPLACE INTO project_meta (key, value) VALUES (?,?)",
                         (key, value))
        conn.commit()
        print("schema ready; project_meta seeded: " + ", ".join(sorted(seed)))
    else:
        print("schema ready")
    conn.close()


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
        cur = conn.execute(
            "INSERT OR IGNORE INTO districts (district, jurisdiction, submitted, "
            "expected_initial_response, status, acknowledged, records_received, "
            "public_note, records_url, last_public_update, fee_estimate, appeal_note) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (row["district"], row["jurisdiction"], row["submitted"],
             row.get("expected_initial_response"), row["status"],
             row.get("acknowledged"), 1 if row.get("records_received") else 0,
             row.get("public_note") or "", row.get("records_url"),
             row.get("last_public_update") or row["submitted"],
             row.get("fee_estimate"), row.get("appeal_note")))
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


def cmd_migrate(args):
    """Idempotent schema upgrade: relax the status CHECK (SQLite cannot ALTER
    a CHECK, so districts is rebuilt) and add fee_estimate/appeal_note columns
    plus the documents table."""
    conn = open_db()
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(districts)").fetchall()}
    has_docs = bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='documents'").fetchone())
    if "fee_estimate" in cols and has_docs:
        print("schema current: 10 statuses, fee_estimate/appeal_note, documents present")
        conn.close()
        return
    if "fee_estimate" not in cols:
        conn.execute("DROP TABLE IF EXISTS districts_new")
        conn.executescript(DISTRICTS_DDL.replace(
            "CREATE TABLE IF NOT EXISTS districts", "CREATE TABLE districts_new"))
        conn.execute(
            "INSERT INTO districts_new (id, district, jurisdiction, submitted, "
            "expected_initial_response, status, acknowledged, records_received, "
            "public_note, records_url, last_public_update, excluded) "
            "SELECT id, district, jurisdiction, submitted, expected_initial_response, "
            "status, acknowledged, records_received, public_note, records_url, "
            "last_public_update, excluded FROM districts")
        conn.execute("DROP TABLE districts")
        conn.execute("ALTER TABLE districts_new RENAME TO districts")
    if not has_docs:
        conn.executescript(DOCUMENTS_DDL)
    conn.commit()
    conn.close()
    print("migrated: status CHECK relaxed (routing_portal, response_fee_estimate, "
          "appeal_filed), fee_estimate + appeal_note added, documents created")


DEFAULT_DOC_LABELS = {
    "request": "Original Georgia Open Records request",
    "response": "District response",
    "appeal": "Appeal or follow-up correspondence",
}


def cmd_add_document(args):
    if args.kind not in ("request", "response", "appeal"):
        sys.exit("--kind must be request, response, or appeal")
    if bool(args.file) == bool(args.url):
        sys.exit("pass exactly one of --file or --url")
    conn = open_db()
    row = _get_row(conn, args.name)
    label = args.label or DEFAULT_DOC_LABELS[args.kind]
    if args.url:
        url = args.url
    else:
        filename = args.filename or os.path.basename(args.file)
        base = os.path.splitext(filename)[0]
        c = wp_api.client()
        found = c.call(
            "GET", f"/wp/v2/media?search={urllib.parse.quote(base)}&per_page=10", quiet=True)
        url = None
        for m in found:
            src = m.get("source_url") or ""
            if os.path.splitext(os.path.basename(src))[0] == base:
                url = src
                print(f"reusing existing media: {url}")
                break
        if url is None:
            with open(args.file, "rb") as f:
                data = f.read()
            media = c.upload_media(filename, data)
            url = media["source_url"]
            print(f"uploaded media: {url}")
    conn.execute(
        "INSERT OR REPLACE INTO documents (district, kind, label, url) VALUES (?,?,?,?)",
        (row["district"], args.kind, label, url))
    conn.commit()
    conn.close()
    print(f"document linked: {row['district']} / {args.kind} -> {url}")


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
    fields = {"status": args.status, "last_public_update": today}
    if args.clear_ack:
        fields["acknowledged"] = None
    _stamp(conn, row, fields)
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
    routing = conn.execute("SELECT COUNT(*) c FROM districts WHERE excluded=0 AND status='routing_portal'").fetchone()["c"]
    appeal = conn.execute("SELECT COUNT(*) c FROM districts WHERE excluded=0 AND "
                          "(status LIKE 'appeal%' OR (appeal_note IS NOT NULL AND appeal_note != ''))").fetchone()["c"]
    response = conn.execute("SELECT COUNT(*) c FROM districts WHERE excluded=0 AND status='response_fee_estimate'").fetchone()["c"]
    conn.close()
    print(f"total={total}, acknowledged={ack}, awaiting={awaiting}, productions={prod}, "
          f"routing={routing}, appeal={appeal}, response={response}")


def _project_and_rows(conn):
    meta = dict(conn.execute("SELECT key, value FROM project_meta").fetchall())
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM districts WHERE excluded=0 ORDER BY district").fetchall()]
    project = {
        "name": meta.get("name", "Georgia Student Settlement Records Project"),
        "owner": meta.get("owner", "Parent Data Force"),
        "contact_email": meta.get("contact_email", bsp.CONTACT),
        "request_window_start": meta.get("request_window_start", "2026-09-25"),
        "request_set_id": meta.get("request_set_id", ""),
        # Zero-district launch: no rows yet, so no max() exists; build_blocks
        # falls back to request_window_start for the "last updated" stamp.
        "snapshot_date": max(r["last_public_update"] for r in rows) if rows else None,
        "district_count": len(rows),
        "acknowledged_count": sum(1 for r in rows if r["status"] == "acknowledged"),
        "production_count": sum(1 for r in rows if r.get("records_url")),
    }
    return project, rows


def _publish(project, rows, status, documents=()):
    try:
        qconn = ga_queue_db.open_db()
        queue = [dict(r) for r in qconn.execute(
            "SELECT * FROM queue WHERE queued=1").fetchall()]
        tvotes = {r["district"].strip().lower(): r["votes"] for r in qconn.execute(
            "SELECT district, votes FROM tracker_votes").fetchall()}
        qconn.close()
    except sqlite3.OperationalError:
        sys.exit("queue DB missing — run: python ga_queue_db.py init")
    queue = bsp.queue_rows(rows, queue)
    content = bsp.build_blocks(project, rows, documents=documents, queue=queue,
                               tracker_votes=tvotes)
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
    documents = [dict(d) for d in conn.execute(
        "SELECT district, kind, label, url FROM documents ORDER BY district, kind").fetchall()]
    conn.close()
    # build_blocks expects the snapshot row shape (booleans, no excluded col).
    for r in rows:
        r["records_received"] = bool(r.pop("records_received"))
    _publish(project, rows, args.status, documents)


def cmd_export_json(args):
    conn = open_db()
    project, rows = _project_and_rows(conn)
    documents = [dict(d) for d in conn.execute(
        "SELECT district, kind, label, url FROM documents ORDER BY district, kind").fetchall()]
    conn.close()
    snap = {"project": project, "districts": [
        {
            "district": r["district"],
            "jurisdiction": r["jurisdiction"],
            "submitted": r["submitted"],
            "expected_initial_response": r["expected_initial_response"],
            "status": r["status"],
            "status_label": STATUS_LABELS.get(r["status"], r["status"]),
            "acknowledged": r["acknowledged"],
            "records_received": bool(r["records_received"]),
            "public_note": r["public_note"],
            "records_url": r["records_url"],
            "last_public_update": r["last_public_update"],
            "fee_estimate": r.get("fee_estimate"),
            "appeal_note": r.get("appeal_note"),
        } for r in rows]}
    if documents:
        snap["documents"] = documents
    with open(args.path, "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"exported {len(rows)} rows -> {args.path}")


# ---- district queue (tools/ga_settlements_queue.sqlite) --------------------

QUEUE_INGESTED_META = "pdforce_ingested"


def cmd_queue(args):
    conn = ga_queue_db.open_db()
    cond = "" if args.history else " WHERE queued=1"
    rows = conn.execute(
        f"SELECT * FROM queue{cond} "
        "ORDER BY first_requested, last_requested DESC, district").fetchall()
    conn.close()
    for r in rows:
        served = "" if r["queued"] else " [served]"
        print(f'{r["district"]} ({r["jurisdiction"]}) · first {r["first_requested"]}'
              f' · last {r["last_requested"]} · requested {r["requested_count"]}× ·'
              f' votes {r["votes"]} · source={r["source"]}{served}')
    print(f"{len(rows)} rows")


def cmd_queue_add(args):
    conn = ga_queue_db.open_db()
    date = args.date or datetime.date.today().isoformat()
    kind = ga_queue_db.upsert(conn, args.name, args.town, note=args.note or "",
                              source=args.source, date=date)
    conn.commit()
    conn.close()
    print(f"queued {args.name}: {kind} ({date})")


def cmd_queue_remove(args):
    conn = ga_queue_db.open_db()
    rows = conn.execute(
        "SELECT * FROM queue WHERE lower(district) LIKE ? AND queued=1 ORDER BY district",
        (f"%{args.name.lower()}%",)).fetchall()
    if not rows:
        sys.exit(f"no queued district matches {args.name!r}")
    if len(rows) > 1:
        cands = ", ".join(r["district"] for r in rows)
        sys.exit(f"ambiguous match for {args.name!r}: {cands}")
    conn.execute("UPDATE queue SET queued=0 WHERE id=?", (rows[0]["id"],))
    conn.commit()
    conn.close()
    print(f"removed {rows[0]['district']} from queue (history kept)")


def _queue_merge():
    """queued=0 for queue rows whose district (case-insensitive, trimmed)
    matches any ga_settlements.sqlite district or shared jurisdiction string.
    Keeps history rows. A merged row's votes move to the tracker-vote store
    under the matching TRACKER district name. Returns (kept, removed)."""
    sconn = open_db()
    tracker = sconn.execute("SELECT district, jurisdiction FROM districts").fetchall()
    sconn.close()
    conn = ga_queue_db.open_db()
    kept = removed = 0
    for q in conn.execute(
            "SELECT id, district, jurisdiction, votes FROM queue WHERE queued=1"
    ).fetchall():
        match = next((t for t in tracker
                      if t["district"].strip().lower() == q["district"].strip().lower()
                      or t["jurisdiction"].strip().lower() == q["jurisdiction"].strip().lower()),
                     None)
        if match:
            if q["votes"]:
                ga_queue_db.vote_tracker(conn, match["district"], amount=q["votes"])
            conn.execute("UPDATE queue SET queued=0 WHERE id=?", (q["id"],))
            removed += 1
        else:
            kept += 1
    conn.commit()
    conn.close()
    return kept, removed


def cmd_queue_merge(args):
    kept, removed = _queue_merge()
    print(f"kept={kept}, removed={removed}")


def cmd_queue_ingest(args):
    """Ingest GA-marked intake/vote posts (ga|district|town|note,
    vote-ga|district). MA posts (plain prefix) are ignored here; MA's
    settlements_db.py queue-ingest ignores GA-marked ones."""
    c = wp_api.client()
    posts = c.call("GET",
                   "/wp/v2/queue-notes?per_page=100&status=private&context=edit",
                   quiet=True)
    conn = ga_queue_db.open_db()
    ingested = skipped = 0
    for m in posts:
        meta = m.get("meta") or {}
        if meta.get(QUEUE_INGESTED_META):
            skipped += 1
            continue
        raw = (m.get("content") or {}).get("raw") or ""
        if not raw.startswith(("ga|", "vote-ga|")):
            skipped += 1  # Massachusetts post or unparseable — not ours
            continue
        date = (m.get("date_gmt") or m.get("date") or "")[:10]
        if not date:
            date = datetime.date.today().isoformat()
        if raw.startswith("vote-ga|"):
            # Interest vote: bump an existing queue row; if the district is
            # already tracked, bump the tracker-vote store instead.
            district = raw[len("vote-ga|"):].split("|", 1)[0].strip()
            if (ga_queue_db.vote(conn, district) is None
                    and ga_queue_db.vote_tracker(conn, district) is None):
                print(f"queue note {m.get('id')}: vote for unknown district "
                      f"{district!r} — skipped", file=sys.stderr)
            c.call("POST", f"/wp/v2/queue-notes/{m['id']}",
                   {"meta": {QUEUE_INGESTED_META: 1}}, quiet=True)
            ingested += 1
            continue
        parts = raw.split("|", 3)
        if len(parts) < 3 or not parts[1].strip():
            print(f"queue note {m.get('id')}: unparseable content — skipped",
                  file=sys.stderr)
            continue
        district = parts[1].strip()
        town = parts[2].strip()
        note = parts[3].strip() if len(parts) > 3 else ""
        ga_queue_db.upsert(conn, district, town, note=note, source="reader", date=date)
        c.call("POST", f"/wp/v2/queue-notes/{m['id']}",
               {"meta": {QUEUE_INGESTED_META: 1}}, quiet=True)
        ingested += 1
    conn.commit()
    conn.close()
    print(f"ingested={ingested}, skipped={skipped}")
    kept, removed = _queue_merge()
    print(f"merge: kept={kept}, removed={removed}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init")
    p.add_argument("--meta", action="store_true",
                   help="seed project_meta with Georgia launch values")
    p.set_defaults(func=cmd_init)
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
    p.add_argument("--clear-ack", action="store_true", dest="clear_ack",
                   help="also clear the acknowledged date (for downgrades)")
    p.set_defaults(func=cmd_mark)
    p = sub.add_parser("add-document")
    p.add_argument("--name", required=True); p.add_argument("--kind", required=True)
    p.add_argument("--file"); p.add_argument("--url")
    p.add_argument("--filename", help="destination filename for upload (default: basename of --file)")
    p.add_argument("--label")
    p.set_defaults(func=cmd_add_document)
    p = sub.add_parser("re-send")
    p.add_argument("--name", required=True)
    p.set_defaults(func=cmd_resend)
    sub.add_parser("stats").set_defaults(func=cmd_stats)
    sub.add_parser("migrate").set_defaults(func=cmd_migrate)
    p = sub.add_parser("publish")
    p.add_argument("--status", choices=("draft", "publish"), default="publish")
    p.set_defaults(func=cmd_publish)
    p = sub.add_parser("export-json")
    p.add_argument("path")
    p.set_defaults(func=cmd_export_json)
    p = sub.add_parser("queue")
    p.add_argument("--history", action="store_true")
    p.set_defaults(func=cmd_queue)
    p = sub.add_parser("queue-add")
    p.add_argument("--name", required=True); p.add_argument("--town", required=True)
    p.add_argument("--note"); p.add_argument("--source", default="reader")
    p.add_argument("--date")
    p.set_defaults(func=cmd_queue_add)
    p = sub.add_parser("queue-remove")
    p.add_argument("--name", required=True)
    p.set_defaults(func=cmd_queue_remove)
    sub.add_parser("queue-merge").set_defaults(func=cmd_queue_merge)
    sub.add_parser("queue-ingest").set_defaults(func=cmd_queue_ingest)
    args = ap.parse_args()
    if args.cmd != "init":
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    args.func(args)


if __name__ == "__main__":
    main()
