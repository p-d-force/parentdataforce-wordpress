#!/usr/bin/env python3
"""Publish the long-form articles as WordPress draft posts.

Converts each Markdown article in the "sped news" workspace with md_to_blocks.py
and creates a draft post via the REST API, assigned the single-long-form
template registered in the pdforce theme.

Entries are idempotent by slug: an existing post (any status) with the same
slug is left untouched and only round-trip-verified. Categories/tags, when
given, are assigned to NEW posts only -- existing posts 15/16/17 are never
modified.

Usage:
  python publish_articles.py            # create missing drafts (idempotent)
  python publish_articles.py --verify   # also GET each draft back and check
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from md_to_blocks import convert, slugify  # noqa: E402
import wp_api  # noqa: E402

TEMPLATE = "single-long-form"

# Category ids (live-verified 2026-09-22): District Data 8, District Reports 10,
# Investigations 6, Policy 7, News 9, Statewide 11.
# Tag ids: Special Education 12, Public Records 13, Funding 14, Transparency 15.
ARTICLES = [
    {
        "path": r"C:/Users/paren/Development/sped news/article1_dese_memo.md",
    },
    {
        "path": r"C:/Users/paren/Development/sped news/article2_student_opportunity_act.md",
    },
    {
        "path": r"C:/Users/paren/Development/sped news/article3_hellman_craven.md",
    },
    {
        "path": r"C:/Users/paren/Development/sped news/article4_seclusion_regs.md",
        "categories": [11, 7],   # Statewide, Policy
        "tags": [12, 15],        # Special Education, Transparency
    },
    {
        "path": r"C:/Users/paren/Development/sped news/article5_fed_cuts_omb.md",
        "categories": [11, 6],   # Statewide, Investigations
        "tags": [13, 15],        # Public Records, Transparency
    },
    {
        "path": r"C:/Users/paren/Development/sped news/article6_stmary_roy.md",
        "categories": [10, 6],   # District Reports, Investigations
        "tags": [13, 15],        # Public Records, Transparency
    },
    {
        "path": r"C:/Users/paren/Development/sped news/article7_segregation_lawsuit.md",
        "categories": [11, 6],   # Statewide, Investigations
        "tags": [15, 12],        # Transparency, Special Education
    },
    {
        "path": r"C:/Users/paren/Development/sped news/article8_cellphone_bill.md",
        "categories": [11, 7],   # Statewide, Policy
        "tags": [12, 14],        # Special Education, Funding
    },
    {
        "path": r"C:/Users/paren/Development/sped news/article9_fy27_budget_soa.md",
        "categories": [11, 7],   # Statewide, Policy
        "tags": [14, 12],        # Funding, Special Education
    },
    {
        "path": r"C:/Users/paren/Development/sped news/article10_settlement_update.md",
        "categories": [8],       # News
        "tags": [13, 15],        # Public Records, Transparency
    },
    {
        "path": r"C:/Users/paren/Development/sped news/article11_settlement_update.md",
        "categories": [9, 8],    # News, District Data
        "tags": [13, 15],        # Public Records, Transparency
    },
    {
        "path": r"C:/Users/paren/Development/sped news/article11b_settlement_update.md",
        "categories": [9, 8],    # News, District Data
        "tags": [13, 15],        # Public Records, Transparency
    },
    {
        "path": r"C:/Users/paren/Development/sped news/article12_settlement_update.md",
        "categories": [9, 8],    # News, District Data
        "tags": [13, 15],        # Public Records, Transparency
    },
]


def find_by_slug(wp, slug):
    res = wp.call("GET", f"/wp/v2/posts?slug={slug}&status=any&per_page=10", quiet=True)
    return res[0] if res else None


def main():
    wp = wp_api.client()
    verify = "--verify" in sys.argv
    results = []

    for entry in ARTICLES:
        path = entry["path"]
        with open(path, encoding="utf-8") as f:
            md = f.read()
        title, _dek, body = convert(md)
        slug = slugify(title)
        existing = find_by_slug(wp, slug)

        if existing:
            pid = existing["id"]
            print(f"skipped (exists): slug={slug} id={pid} status={existing['status']}")
        else:
            payload = {
                "title": title,
                "content": body,
                "status": "draft",
                "slug": slug,
                "template": TEMPLATE,
            }
            if entry.get("categories"):
                payload["categories"] = entry["categories"]
            if entry.get("tags"):
                payload["tags"] = entry["tags"]
            post = wp.call("POST", "/wp/v2/posts", payload, quiet=True)
            pid = post["id"]
            print(f"created draft id={pid} slug={slug} template={post.get('template')!r} len={len(body)}")

        results.append({"id": pid, "slug": slug, "title": title})

        if verify:
            back = wp.call("GET", f"/wp/v2/posts/{pid}?context=edit", quiet=True)
            same = back["content"]["raw"] == body
            print(f"  verify: content round-trip {'OK' if same else 'MISMATCH'}, "
                  f"template={back.get('template')!r}, status={back['status']}")
            assert same, f"content mismatch on post {pid}"
            assert back.get("template") == TEMPLATE, f"template not persisted on {pid}"

    print(json.dumps(results, indent=1))


if __name__ == "__main__":
    main()
