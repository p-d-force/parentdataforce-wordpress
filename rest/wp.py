#!/usr/bin/env python3
"""
WordPress REST API client for parentdataforce.com /wordpress/.

Auth: HTTP Basic Auth using the Application Password from credentials.json
(must sit next to this script). No third-party dependencies.

Usage:
  wp.py whoami                          # authenticated REST identity
  wp.py posts [--limit N] [--status S] [--page P]
  wp.py get-post --id N
  wp.py new-post --title T [--content HTML] [--status publish] [--slug S] [--categories IDS]
  wp.py update-post --id N [--title T] [--content HTML] [--status S] [--slug S] [--categories IDS]
  wp.py delete-post --id N [--force]
  wp.py pages [--limit N]
  wp.py get-page --id N
  wp.py new-page --title T [--content HTML] [--status publish]
  wp.py delete-page --id N [--force]
  wp.py terms [--taxonomy categories|tags]
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def load_creds():
    path = os.path.join(HERE, "credentials.json")
    if not os.path.exists(path):
        print(f"credentials.json not found in {HERE}", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class WP:
    def __init__(self, c):
        self.base = c["rest_url"].rstrip("/")
        tok = base64.b64encode(f"{c['username']}:{c['application_password']}".encode()).decode()
        self.auth = f"Basic {tok}"

    def call(self, method, path, data=None):
        url = self.base + path
        body = json.dumps(data).encode() if data is not None else None
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", self.auth)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw, code = r.read().decode(), r.getcode()
        except urllib.error.HTTPError as e:
            raw, code = e.read().decode(), e.code
        except urllib.error.URLError as e:
            print(f"Request failed: {e.reason}", file=sys.stderr)
            sys.exit(1)
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            obj = raw
        if code >= 400:
            msg = json.dumps(obj, ensure_ascii=False) if isinstance(obj, dict) else obj
            print(f"[HTTP {code}] {msg}", file=sys.stderr)
            sys.exit(code)
        print(json.dumps(obj, ensure_ascii=False, indent=2))
        return obj


def keep(d):
    return {k: v for k, v in d.items() if v is not None}


def main():
    wp = WP(load_creds())
    p = argparse.ArgumentParser(description="WordPress REST API client")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("whoami").set_defaults(fn=lambda a: wp.call("GET", "/wp/v2/users/me"))

    s = sub.add_parser("posts")
    s.add_argument("--limit", type=int, default=10)
    s.add_argument("--status")
    s.add_argument("--page", type=int)

    def _posts(a):
        q = f"/wp/v2/posts?per_page={a.limit}"
        if a.page:
            q += f"&page={a.page}"
        if a.status:
            q += f"&status={a.status}"
        wp.call("GET", q)
    s.set_defaults(fn=_posts)

    g = sub.add_parser("get-post")
    g.add_argument("--id", type=int, required=True)
    g.set_defaults(fn=lambda a: wp.call("GET", f"/wp/v2/posts/{a.id}"))

    n = sub.add_parser("new-post")
    n.add_argument("--title"); n.add_argument("--content")
    n.add_argument("--status", default="publish"); n.add_argument("--slug")
    n.add_argument("--categories")
    n.set_defaults(fn=lambda a: wp.call(
        "POST", "/wp/v2/posts",
        keep({"title": a.title, "content": a.content, "status": a.status,
              "slug": a.slug,
              "categories": int(a.categories) if a.categories else None})))

    u = sub.add_parser("update-post")
    u.add_argument("--id", type=int, required=True); u.add_argument("--title")
    u.add_argument("--content"); u.add_argument("--status")
    u.add_argument("--slug"); u.add_argument("--categories")
    u.set_defaults(fn=lambda a: wp.call(
        "PUT", f"/wp/v2/posts/{a.id}",
        keep({"title": a.title, "content": a.content, "status": a.status,
              "slug": a.slug,
              "categories": int(a.categories) if a.categories else None})))

    d = sub.add_parser("delete-post")
    d.add_argument("--id", type=int, required=True); d.add_argument("--force", action="store_true")
    d.set_defaults(fn=lambda a: wp.call("DELETE", f"/wp/v2/posts/{a.id}?force={str(a.force).lower()}"))

    sp = sub.add_parser("pages")
    sp.add_argument("--limit", type=int, default=10); sp.add_argument("--page", type=int)

    def _pages(a):
        q = f"/wp/v2/pages?per_page={a.limit}"
        if a.page:
            q += f"&page={a.page}"
        wp.call("GET", q)
    sp.set_defaults(fn=_pages)

    gp = sub.add_parser("get-page")
    gp.add_argument("--id", type=int, required=True)
    gp.set_defaults(fn=lambda a: wp.call("GET", f"/wp/v2/pages/{a.id}"))

    np_ = sub.add_parser("new-page")
    np_.add_argument("--title"); np_.add_argument("--content"); np_.add_argument("--status", default="publish")
    np_.set_defaults(fn=lambda a: wp.call("POST", "/wp/v2/pages", keep({"title": a.title, "content": a.content, "status": a.status})))

    dp = sub.add_parser("delete-page")
    dp.add_argument("--id", type=int, required=True); dp.add_argument("--force", action="store_true")
    dp.set_defaults(fn=lambda a: wp.call("DELETE", f"/wp/v2/pages/{a.id}?force={str(a.force).lower()}"))

    t = sub.add_parser("terms")
    t.add_argument("--taxonomy", default="categories", choices=["categories", "tags"])
    def _terms(a):
        wp.call("GET", f"/wp/v2/{a.taxonomy}")
    t.set_defaults(fn=_terms)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
