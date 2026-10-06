#!/usr/bin/env python3
"""Build the /articles/ index: every published WordPress post, grouped by section.

The listings are real core/query loops, so a newly published post appears
without rebuilding anything. Section membership is a category filter; the
per-section `exclude` lists are computed from the live REST inventory so that a
post which carries several categories is shown exactly once, in its first home.

Block helpers are shared with build_worcester_page.py / build_weston_page.py.

Usage:
  python build_articles_page.py --status draft
  python build_articles_page.py --status publish
"""
import argparse
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wp_api

SLUG = "articles"
TITLE = "Articles"
PAGE_TEMPLATE = "page-no-title"
CONTACT = "joey@parentdataforce.com"
UPDATED = "October 1, 2026"

PROJECTS_URL = "https://www.parentdataforce.com/projects/"
DONATE_URL = "https://www.parentdataforce.com/donate/"
MAILTO_CONTACT = ("mailto:joey@parentdataforce.com"
                  "?subject=Articles%20page%20feedback")

# Category ids are live-verified; names are resolved at build time so a rename
# in wp-admin cannot silently break the sections.
SECTIONS = [
    ("Statewide & policy", 11, 12, "The rules, the budget, and the litigation "
     "that set the terms for everything else on this site."),
    ("Investigations & records", 6, 12, "Records projects where the reporting "
     "followed a district's own paperwork into the record."),
    ("Public records", 16, 12, "Requests, appeals, and fee fights — what it "
     "costs to see what a district did."),
    ("District records", 8, 30, "The settlement-records project, one district "
     "response at a time."),
    ("More from the record", 9, 30, "Everything else we publish."),
]

PAGE_CSS = """<style>
/* Articles index — page-scoped. Tokens only, so the Paper and Split
   variations keep working. The grid reproduces .pdf-cardgrid exactly. */
.art-hero{padding-top:2.5rem}
.art-updated{margin:.25rem 0 0;color:var(--pdf-mid,#a0a0a0);font-size:.8125rem}
.art-section{padding-top:var(--wp--preset--spacing--60,3rem);padding-bottom:var(--wp--preset--spacing--60,3rem)}
.art-section h2{margin:0 0 .35rem;font-size:clamp(1.5rem,3vw,2.1rem);line-height:1.15;letter-spacing:-0.015em}
.art-section .art-blurb{margin:0 0 1.5rem;color:var(--pdf-mid);font-size:.9375rem;max-width:46rem}
.pdf-qgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--pdf-line);border:1px solid var(--pdf-line);align-items:stretch}
.pdf-qgrid .wp-block-post-template{display:contents}
.pdf-qgrid .pdf-card-excerpt{display:flex;flex-direction:column;flex:1 1 auto}
.pdf-qgrid .pdf-card-excerpt>.wp-block-post-excerpt__excerpt{display:flex;flex-direction:column;flex:1 1 auto}
.pdf-qgrid .pdf-card-excerpt a{margin-top:auto;padding-top:.9rem;display:inline-block;font-family:var(--pdf-mono);font-size:.6875rem;letter-spacing:.18em;text-transform:uppercase;color:var(--pdf-signal-hi);text-decoration:none}
.pdf-qgrid .pdf-card-excerpt a:hover{color:var(--pdf-signal)}
.art-empty{color:var(--pdf-mid);font-style:italic}
@media (max-width:1100px){.pdf-qgrid{grid-template-columns:repeat(2,1fr)}}
@media (max-width:719px){.pdf-qgrid{grid-template-columns:1fr}}
</style>"""


def esc(t):
    return html.escape(str(t), quote=False)


def attr(t):
    return html.escape(str(t), quote=True)


def p(text, class_name=None):
    open_tag = (f'<!-- wp:paragraph {{"className":"{class_name}"}} -->'
                if class_name else "<!-- wp:paragraph -->")
    cls = f' class="{attr(class_name)}"' if class_name else ""
    return f"{open_tag}\n<p{cls}>{text}</p>\n<!-- /wp:paragraph -->"


def h(level, text):
    return (f'<!-- wp:heading {{"level":{level}}} -->\n'
            f'<h{level} class="wp-block-heading">{text}</h{level}>\n'
            f"<!-- /wp:heading -->")


def group(inner, attrs="", class_name=None):
    open_comment = f"<!-- wp:group {attrs} -->" if attrs else "<!-- wp:group -->"
    div_cls = "wp-block-group" + (f" {class_name}" if class_name else "")
    return f'{open_comment}\n<div class="{div_cls}">{inner}</div>\n<!-- /wp:group -->'


def html_block(raw):
    return f"<!-- wp:html -->\n{raw}\n<!-- /wp:html -->"


def buttons(items):
    parts = []
    for label, href, outline in items:
        cls = ' {"className":"is-style-outline"}' if outline else ""
        div = "wp-block-button is-style-outline" if outline else "wp-block-button"
        parts.append(
            f"<!-- wp:button{cls} -->\n"
            f'<div class="{div}"><a class="wp-block-button__link '
            f'wp-element-button" href="{attr(href)}">{label}</a></div>\n'
            f"<!-- /wp:button -->")
    return ('<!-- wp:buttons -->\n'
            f'<div class="wp-block-buttons">{"".join(parts)}</div>\n<!-- /wp:buttons -->')


CARD = "\n".join([
    '<!-- wp:post-terms {"term":"category","className":"pdf-card-tag"} /-->',
    '<!-- wp:post-title {"level":3,"isLink":true,"className":"pdf-card-title"} /-->',
    '<!-- wp:post-date {"format":"M j","className":"pdf-card-meta"} /-->',
    '<!-- wp:post-excerpt {"moreText":"Read the record →","excerptLength":34,'
    '"showMoreOnNewLine":true,"className":"pdf-card-excerpt"} /-->',
])

CARD_BLOCK = ('<!-- wp:group {"className":"pdf-card","layout":{"type":"default"}} -->\n'
              '<div class="wp-block-group pdf-card">\n'
              + CARD + "\n</div>\n<!-- /wp:group -->")

TEMPLATE = ('<!-- wp:post-template {"className":"pdf-cardgrid","layout":{"type":"default"}} -->\n'
            '<div class="wp-block-post-template pdf-cardgrid">\n'
            + CARD_BLOCK + "\n"
            '<!-- /wp:post-template -->')



def inventory(c):
    """category id -> set of post ids, plus every post id."""
    names = {t["id"]: t["name"] for t in
             c.call("GET", "/wp/v2/categories?per_page=100", quiet=True)}
    posts = c.call("GET", "/wp/v2/posts?per_page=100&page=1&status=publish", quiet=True)
    by_cat = {}
    for post in posts:
        for cid in post.get("categories", []):
            by_cat.setdefault(cid, set()).add(post["id"])
    return names, by_cat, posts


def query_loop(qid, category, per_page, exclude):
    # Verified against core on this install: the category filter is
    # `categoryIds` inside the `query` object. `metadata.categories` and a
    # `tax_query` inside the block both render unfiltered — do not use them.
    # `exclude` maps to post__not_in and is what keeps a post that carries
    # several categories to a single section.
    q = {"queryId": qid,
         "query": {"perPage": per_page, "pages": 0, "offset": 0, "postType": "post",
                   "order": "desc", "orderBy": "date", "author": "", "search": "",
                   "exclude": exclude, "sticky": "", "inherit": False,
                   "categoryIds": [category]},
         "className": "pdf-qgrid"}
    return ('<!-- wp:query ' + json.dumps(q, separators=(",", ":"), ensure_ascii=False) + ' -->\n'
            '<div class="wp-block-query pdf-qgrid">\n'
            + TEMPLATE + "\n</div>\n<!-- /wp:query -->")


def build_blocks(c):
    names, by_cat, posts = inventory(c)
    total = len(posts)
    claimed = set()

    blocks = [PAGE_CSS]

    hero = "\n".join([
        p("Writing", class_name="pdf-kicker"),
        h(1, esc(TITLE)),
        p("Newest first within each section. These are the records projects, "
          "the district responses, and the state and federal developments "
          "that change what parents can get. All of it is drawn from public "
          "records."),
        buttons([
            ("Projects", PROJECTS_URL, True),
            ("Donate", DONATE_URL, True),
        ]),
        p(f"Last updated: {UPDATED}", class_name="art-updated"),
    ])
    blocks.append(group(hero, attrs='{"align":"wide","className":"pdf-band art-hero"}',
                        class_name="pdf-band art-hero"))

    for label, cat_id, per_page, blurb in SECTIONS:
        members = by_cat.get(cat_id, set())
        exclude = sorted(claimed & members)
        claimed |= members
        body = query_loop(cat_id, cat_id, per_page, exclude)
        blocks.append(group(
            h(2, esc(label)) + "\n"
            + p(blurb, class_name="art-blurb") + "\n"
            + body,
            attrs='{"align":"wide","className":"pdf-band art-section"}',
            class_name="pdf-band art-section"))
        print("section %-26s cat=%-3s members=%-3d excluded=%d"
              % (label, cat_id, len(members), len(exclude)))

    unclaimed = {p_["id"] for p_ in posts} - claimed
    print("total posts=%d claimed=%d unclaimed=%s" % (total, len(claimed), sorted(unclaimed)))
    assert not unclaimed, "posts outside every section: %s" % sorted(unclaimed)

    cta = "\n".join([
        h(2, "Missing something?"),
        p("Every article here came out of a records request. If you have a "
          "document from a district — a response, a determination, a filing, or "
          "something they produced after we asked — send it in and we will use "
          "it."),
        buttons([(f"Email {CONTACT}", MAILTO_CONTACT, False),
                 ("All projects", PROJECTS_URL, True),
                 ("Donate", DONATE_URL, True)]),
    ])
    blocks.append(group(cta, attrs='{"align":"wide","className":"pdf-band"}',
                        class_name="pdf-band"))
    return "\n\n".join(blocks) + "\n", total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", choices=("draft", "publish"), default="publish")
    args = ap.parse_args()

    c = wp_api.client()
    content, total = build_blocks(c)

    existing = c.call("GET",
                      f"/wp/v2/pages?slug={SLUG}&status=publish,draft,pending,private&per_page=10",
                      quiet=True)
    payload = {"title": TITLE, "content": content, "status": args.status,
               "template": PAGE_TEMPLATE}
    if existing:
        result = c.call("POST", f"/wp/v2/pages/{existing[0]['id']}", payload, quiet=True)
        action = "updated"
    else:
        payload["slug"] = SLUG
        result = c.call("POST", "/wp/v2/pages", payload, quiet=True)
        action = "created"

    print(json.dumps({"action": action, "id": result["id"], "link": result["link"],
                      "status": result["status"], "template": result.get("template"),
                      "sections": len(SECTIONS), "posts": total,
                      "content_chars": len(content)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())