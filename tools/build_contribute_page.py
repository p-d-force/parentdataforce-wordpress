#!/usr/bin/env python3
"""Build and idempotently publish the Ways to contribute page on
parentdataforce.com/news.

The page body lives in the theme pattern `pdforce/contribute`
(theme/pdforce/patterns/contribute.php); this script only upserts the page
shell around it, so copy and layout are edited in the pattern, not here.

Usage (run from tools/):

    python build_contribute_page.py [--status draft|publish]

Stdlib only. Credentials come from ../rest/credentials.json via wp_api.
"""
import argparse
import json

import wp_api

SLUG = "contribute"
TITLE = "Ways to contribute"
PAGE_TEMPLATE = "page-no-title"
CONTACT = "joey@parentdataforce.com"

PATTERN_REF = '<!-- wp:pattern {"slug":"pdforce/contribute"} /-->'


def build_blocks():
    return PATTERN_REF + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--status", choices=("draft", "publish"), default="publish")
    args = ap.parse_args()

    content = build_blocks()

    c = wp_api.client()
    existing = c.call(
        "GET",
        f"/wp/v2/pages?slug={SLUG}&status=publish,draft,pending,private&per_page=10",
        quiet=True,
    )
    payload = {"title": TITLE, "content": content, "status": args.status,
               "template": PAGE_TEMPLATE}
    if existing:
        page = existing[0]
        result = c.call("POST", f"/wp/v2/pages/{page['id']}", payload, quiet=True)
        action = "updated"
    else:
        payload["slug"] = SLUG
        result = c.call("POST", "/wp/v2/pages", payload, quiet=True)
        action = "created"

    print(json.dumps({
        "action": action,
        "id": result["id"],
        "link": result["link"],
        "status": result["status"],
        "template": result.get("template"),
        "contact": CONTACT,
        "content_chars": len(content),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()