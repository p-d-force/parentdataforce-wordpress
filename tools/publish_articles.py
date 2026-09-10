#!/usr/bin/env python3
"""Publish the long-form articles as WordPress draft posts.

Converts each Markdown article in the "sped news" workspace with md_to_blocks.py
and creates a draft post via the REST API, assigned the single-long-form
template registered in the pdforce theme.

Usage:
  python publish_articles.py            # create the three drafts
  python publish_articles.py --verify   # GET each draft back and check content
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from md_to_blocks import convert, slugify  # noqa: E402
import wp_api  # noqa: E402

ARTICLES = [
    r"C:/Users/paren/Development/sped news/article1_dese_memo.md",
    r"C:/Users/paren/Development/sped news/article2_student_opportunity_act.md",
    r"C:/Users/paren/Development/sped news/article3_hellman_craven.md",
]

TEMPLATE = "single-long-form"


def main():
    wp = wp_api.client()
    verify = "--verify" in sys.argv
    results = []

    for path in ARTICLES:
        with open(path, encoding="utf-8") as f:
            md = f.read()
        title, _dek, body = convert(md)
        slug = slugify(title)
        post = wp.call("POST", "/wp/v2/posts", {
            "title": title,
            "content": body,
            "status": "draft",
            "slug": slug,
            "template": TEMPLATE,
        }, quiet=True)
        pid = post["id"]
        results.append((pid, slug, title, len(body)))
        print(f"created draft id={pid} slug={slug} template={post.get('template')!r} len={len(body)}")

        if verify:
            back = wp.call("GET", f"/wp/v2/posts/{pid}?context=edit", quiet=True)
            same = back["content"]["raw"] == body
            print(f"  verify: content round-trip {'OK' if same else 'MISMATCH'}, "
                  f"template={back.get('template')!r}, status={back['status']}")
            assert same, f"content mismatch on post {pid}"
            assert back.get("template") == TEMPLATE, f"template not persisted on {pid}"

    print(json.dumps([{"id": r[0], "slug": r[1], "title": r[2]} for r in results], indent=1))


if __name__ == "__main__":
    main()
