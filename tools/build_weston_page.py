#!/usr/bin/env python3
"""Build and idempotently publish the Weston DEI Records Project hub.

Mirrors build_worcester_page.py: same block helpers, same upsert shape, same
media-library lookup, same print-JSON contract. Stdlib only.

Usage:
  python build_weston_page.py --status draft
  python build_weston_page.py --status publish
"""
import argparse
import html
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wp_api

SLUG = "weston-dei-records-project"
TITLE = "Weston Public Schools DEI Records Project"
PAGE_TEMPLATE = "page-no-title"
CONTACT = "joey@parentdataforce.com"

ARTICLE_URL = ("https://www.parentdataforce.com/"
               "weston-dei-coordinator-records-fee-dispute/")
PROJECTS_URL = "https://www.parentdataforce.com/projects/"
DONATE_URL = "https://www.parentdataforce.com/donate/"
MAILTO_CONTACT = (
    "mailto:joey@parentdataforce.com"
    "?subject=Weston%20DEI%20records%20fee%20dispute"
)

UPDATED = "October 1, 2026"

# Exhibit images, uploaded by the project build. Keyed by exhibit number so the
# gallery stays readable; values are the media filenames resolved in the library.
EXHIBITS = {
    "01": ("The purpose sentence of the July 31, 2026 request: to understand "
           "the functions, projects, activities, recommendations, and work "
           "product associated with the DEI Coordinator position.",
           "weston-exhibit-01.png"),
    "02": ("The fee-waiver and rolling-production language of the same request, "
           "including the request for a written, itemized, good-faith estimate "
           "before chargeable work begins.",
           "weston-exhibit-02.png"),
    "03": ("The August 14, 2026 response, under the heading “Fee Estimate,” "
           "stating that Weston employees have already spent several hours "
           "searching for responsive records.",
           "weston-exhibit-03.png"),
    "04": ("The August 14, 2026 estimate as written: a 10,000-page minimum, "
           "166.66 review hours, 214.66 hours at $25 per hour, a $50.00 copying "
           "subtotal, and a total of $5,416.67.",
           "weston-exhibit-04.png"),
    "05": ("The August 28, 2026 supplemental response: “The District did not "
           "conduct electronic searches for purposes of its fee estimate.”",
           "weston-exhibit-05.png"),
    "06": ("The August 28, 2026 SPR26/3192 determination closing the first "
           "appeal because the district had issued a new response, and "
           "preserving the right to appeal that response.",
           "weston-exhibit-06.png"),
    "07": ("Page 4 of the September 14, 2026 SPR26/3432 determination, quoting "
           "the district's own account of how the estimate was reached.",
           "weston-exhibit-07.png"),
    "08": ("Page 5 of the SPR26/3432 determination, quoting the 2023 Suffolk "
           "Superior Court Friedman decision on the duty to produce responsive "
           "materials in a rolling fashion.",
           "weston-exhibit-08.png"),
    "09": ("The conclusion of the SPR26/3432 determination: the appeal is "
           "closed, with an invitation to narrow the request and a note that any "
           "revision would require a revised fee estimate.",
           "weston-exhibit-09.png"),
    "10": ("The September 23, 2026 Public Records Division acknowledgement: the "
           "decision on the reconsideration will be due 15 business days from "
           "the day the request was received.",
           "weston-exhibit-10.png"),
}

STATS = [
    ("July 31, 2026", "request filed"),
    ("$5,416.67", "fee estimate"),
    ("10,000", "minimum pages assumed"),
    ("0", "electronic searches for the estimate"),
    ("SPR26/3432", "determination, Sept 14"),
    ("Pending", "reconsideration"),
]

TIMELINE = [
    "<strong>July 31, 2026 — the request.</strong> Sent at about 10:02 p.m. "
    "Eastern to Records Access Officer Neil Trahan, covering Shannon Sheldon’s "
    "first three months as Weston’s DEI Coordinator, September 18 through "
    "December 18, 2023. Five enumerated record categories, express exclusions "
    "for student personally identifiable information and private personnel "
    "information, and a request for native electronic production with no single "
    "flattened PDF portfolio.",
    "<strong>August 14, 2026 — the response and the fee.</strong> Weston "
    "objected that terms including “concerning,” “materially contributed "
    "to,” and “work-related” were insufficiently specific, summarized the "
    "request as essentially all documents that in any way relate to the "
    "employee or the position, stated that employees had "
    "<strong>already spent several hours searching</strong>, and issued a fee "
    "estimate of <strong>$5,416.67</strong> requiring advance payment. No "
    "production date was given.",
    "<strong>August 14, 2026 — two more filings.</strong> A second request "
    "sought the search logs, query logs, hit counts, inventories, worksheets, "
    "and calculations underlying the estimate. An appeal to the Supervisor of "
    "Records challenged the specificity objection, the grounding of the fee, "
    "the conversion of native records, the copying charge, the breadth of the "
    "assumed redaction time, the absence of rolling production, and the "
    "public-interest fee waiver. It became <strong>SPR26/3192</strong>.",
    "<strong>August 17, 2026 — acknowledged.</strong> The Public Records "
    "Division acknowledged the appeal and notified Weston.",
    "<strong>August 28, 2026 — the supplemental response.</strong> Weston "
    "issued a four-page response that both supplemented the July 31 request and "
    "answered the methodology request. It identified the basis of the estimate "
    "as internal discussions, advice of counsel, employee knowledge of "
    "electronic systems, prior experience, and the district’s understanding of "
    "the request — and then stated that "
    "<strong>“The District did not conduct electronic searches for purposes of "
    "its fee estimate.”</strong> It reported no written methodology "
    "communications except potentially privileged ones, and no other versions "
    "of the estimate. The $5,416.67 was not withdrawn.",
    "<strong>August 28, 2:08 p.m. — supplemental submission.</strong> A "
    "supplemental submission in SPR26/3192 was filed addressing the new August "
    "28 response.",
    "<strong>August 28, 2:20 p.m. — SPR26/3192 closed.</strong> The "
    "determination closed the appeal because the district had issued a further "
    "response, and preserved the right to appeal that response. It was a "
    "procedural closure, not a ruling on the merits of the fee.",
    "<strong>August 28, 2:51 p.m. — reconsideration sought.</strong> Parent "
    "Data Force wrote that the 2:08 submission did not appear to have been "
    "considered, and requested reconsideration.",
    "<strong>August 28, 3:03 p.m. — second appeal.</strong> A new appeal of "
    "the August 28 response was filed, arguing that it did not cure the "
    "original defects and in several respects confirmed them.",
    "<strong>August 29, 2026 — the paraphrase supplement.</strong> A narrow "
    "supplement argued that Weston’s characterization — essentially all "
    "documents that in any way relate — was broader than the July 31 request, "
    "which named one employee, one position, one three-month period, five "
    "categories, exclusions, and production instructions.",
    "<strong>August 31, 2026 — SPR26/3432 opened.</strong> The new appeal was "
    "acknowledged and assigned docket <strong>SPR26/3432</strong>.",
    "<strong>September 14, 2026 — the determination.</strong> The Supervisor "
    "recited the municipal fee rules and both parties’ positions, then found the "
    "request <strong>very broad in scope</strong>, quoted the 2023 *Friedman* "
    "decision, encouraged the parties to communicate and potentially narrow the "
    "request, noted that any revision would require a revised fee estimate, and "
    "closed the appeal. It did not rule that the estimate was lawful.",
    "<strong>September 18, 2026 — reconsideration.</strong> Reconsideration of "
    "SPR26/3432 in its entirety was requested, raising twenty substantive "
    "issues including the later published 2024 Appeals Court decision in "
    "*Friedman* and a § 10(e) theory that a non-compliant day-ten response does "
    "not preserve fee authority.",
    "<strong>September 23, 2026 — acknowledged.</strong> Assistant Director "
    "Barbara Durgin acknowledged the reconsideration and stated that under SPR "
    "Bulletin 04-17 the decision would be due 15 business days from the day the "
    "request was received. No reconsideration determination has been located.",
]

ESTABLISHED = [
    "Weston created and funded a Diversity, Equity, and Inclusion Coordinator "
    "position held by Shannon Sheldon, whose first three months ran from "
    "September 18 through December 18, 2023.",
    "On July 31, 2026, Parent Data Force submitted a request limited to one "
    "named employee, one position, one three-month period and five enumerated "
    "record categories, expressly disclaiming student personally identifiable "
    "information and private personnel information, and asking for native "
    "electronic production with no single flattened PDF portfolio.",
    "On August 14, 2026 the district objected to specificity, stated its "
    "employees had “already spent several hours searching,” and issued a "
    "$5,416.67 fee estimate requiring advance payment, with no production date.",
    "That estimate was built from 40 search hours, a 10,000-page minimum, "
    "166.66 review hours at one minute per page, 8 conversion hours, and $25 "
    "per hour, plus $50 for at least 1,000 copied pages.",
    "On August 28, 2026 the district stated: “The District did not conduct "
    "electronic searches for purposes of its fee estimate.” It also stated "
    "there were no written methodology communications except potentially "
    "privileged ones and no versions of the estimate with different figures. It "
    "did not withdraw the estimate.",
    "SPR26/3192 was closed procedurally on August 28 because the district had "
    "issued a new response, with the substance of that response preserved for "
    "appeal. A supplemental submission at 2:08 p.m. preceded that determination "
    "at 2:20 p.m.",
    "The September 14, 2026 determination recited the fee rules and both "
    "parties’ positions, found the request very broad, quoted *Friedman*, "
    "encouraged narrowing, and closed the appeal.",
    "That determination did not rule that the estimate was lawful, did not "
    "establish the 10,000-page or 166.66-hour figures, did not approve the $50 "
    "copying charge or the $25 rate, and did not decide the § 10(e) theory.",
    "Reconsideration was requested September 18 and acknowledged September 23, "
    "with a decision due 15 business days from receipt. No responsive record "
    "has been produced and no reconsideration determination has issued.",
]

NOT_ESTABLISHED = [
    "It is not established that the fee was unreasonable. No one has so held; "
    "the estimate has never been ordered reduced or waived.",
    "It is not established that the fee was reasonable either. “Not decided” is "
    "not “upheld,” and the September 14 determination expressly declined to "
    "resolve the fee components.",
    "It is not established that the district contradicted itself. August 14 "
    "says employees had already spent several hours searching; August 28 says "
    "no electronic searches were conducted <em>for purposes of the fee "
    "estimate</em>. Both can be true. The relationship between them is "
    "unexplained, which is a narrower claim than a contradiction.",
    "It is not established what the DEI Coordinator actually did. No work "
    "product has been produced — not a job description, not an organizational "
    "chart, not a ninety-day plan, not a single email.",
    "It is not established that the Supervisor ignored the 2:08 p.m. "
    "submission. The twelve-minute gap is established; whether the submission "
    "was considered is unknown.",
    "It is not established that the § 10(e) fee-bar theory will succeed. It is "
    "pending and undecided.",
    "It is not established that the fee would have produced nothing, or "
    "everything. Nobody knows what is in the records.",
    "It is not established anything about the merits of DEI as policy. Nothing "
    "in this record speaks to that question.",
]

REASONABLY_ASSUMED = [
    "The methodology records probably do not exist, or are thin. A district "
    "that had logged hits or built worksheets supporting a 10,000-page floor "
    "would have had a straightforward time to produce them on August 28. An "
    "estimate built from experience and professional judgment is lawful; it is "
    "also an estimate.",
    "The 10,000-page figure probably includes material the request had already "
    "excluded. Automated notifications, all-district mail and scheduling "
    "traffic are the ordinary way a three-month workload acquires five figures.",
    "The 1,000-page copying assumption probably reflects a default rather than "
    "a review. No particular record is identified in either response as "
    "requiring physical copying.",
    "The eight-hour conversion step probably anticipates a workflow the request "
    "asked Weston not to use, since the estimate describes compiling “to a "
    "single file,” saving to another file, and converting.",
    "The narrowing suggestions probably did not narrow. Weston suggested "
    "identifying the employee and time frame in August — both already supplied "
    "by the July 31 request.",
    "The records probably exist. A coordinator’s first three months in a "
    "district that created the position would ordinarily leave job "
    "descriptions, organizational charts, onboarding plans, calendars and sent "
    "email.",
]

OPEN_QUESTIONS = [
    "No responsive record has been produced. Not one category, not one "
    "document.",
    "No production date exists. Neither the August 14 nor the August 28 "
    "response supplied one, and the September 14 determination did not require "
    "one.",
    "No hit count exists. Nothing in the record states how many responsive "
    "records there are.",
    "The 10,000-page minimum has no identified request-specific basis — and so, "
    "derivatively, neither does the 166.66-hour review figure.",
    "The 1,000-page copying assumption has no identified basis.",
    "The two search statements have not been reconciled: whether the earlier "
    "searching was manual, which systems were involved, what it found, and "
    "whether it informed the estimate.",
    "No task-by-task basis for the $25 rate has been shown, and no allocation "
    "of chargeable versus nonchargeable review time.",
    "There has been no ruling on § 10(e).",
    "There has been no reconsideration determination.",
    "The 2024 Massachusetts Appeals Court decision in <em>Friedman</em> has not "
    "been addressed in a determination.",
    "No discrete, readily identifiable category has been separately produced. A "
    "job description, an organizational chart and a first-90-day plan would "
    "cost almost nothing to produce and would answer a meaningful part of the "
    "accountability question.",
]

PAGE_CSS = """<style>
/* Weston DEI Records Project — page-scoped styles.
   Tokens only, so the Paper and Split variations keep working. */
.wrd-hero{padding-top:2.5rem}
.wrd-updated{margin:.25rem 0 0;color:var(--pdf-mid,#a0a0a0);font-size:.8125rem}
.wrd-frame{border:1px solid var(--pdf-line,#2a2a2a);border-left:3px solid var(--pdf-signal,#ff5a1f);background:var(--pdf-ink-1,#161616);padding:0.9rem 1.1rem;margin:1.5rem 0}
.wrd-frame p{margin:0;font-size:0.95rem;line-height:1.55}
.wrd-panel{border:1px solid var(--pdf-line,#2a2a2a);background:var(--pdf-ink-1,#161616);padding:1.5rem 1.25rem;margin:1.5rem 0 0}
.wrd-panel--yes{border-left:3px solid var(--pdf-signal,#ff5a1f)}
.wrd-panel--no{border-left:3px solid var(--pdf-mid,#a0a0a0)}
.wrd-panel--assume{border-left:3px solid var(--pdf-signal-hi,#ffa366)}
.wrd-panel h2{margin-top:0}
.wrd-panel ul{margin-bottom:0}
.wrd-gallery{border:1px solid var(--pdf-line,#2a2a2a);background:var(--pdf-ink-1,#161616);padding:1.25rem;margin:1.5rem 0 0}
.wrd-gallery-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.25rem;margin:0}
.wrd-gallery-grid figure{margin:0}
.wrd-gallery-grid img{width:100%;height:auto;border:1px solid var(--pdf-line,#2a2a2a);border-radius:4px;background:#fff}
.wrd-gallery-grid figcaption{font-size:.8125rem;color:var(--pdf-mid,#a0a0a0);margin-top:.4rem;line-height:1.45}
.wrd-timeline{border:1px solid var(--pdf-line,#2a2a2a);background:var(--pdf-ink-1,#161616);padding:1.5rem 1.25rem;margin:1.5rem 0 0}
.wrd-timeline li{margin-bottom:.85rem}
.wrd-timeline li:last-child{margin-bottom:0}
.wrd-stat-range{font-size:1.125rem;letter-spacing:.01em;line-height:1.25;padding-top:.45rem}
.wrd-cta{border:1px solid var(--pdf-line,#2a2a2a);background:var(--pdf-ink-1,#161616);padding:1.5rem;margin:1.5rem 0 0}
@media (max-width:719px){.wrd-gallery-grid{grid-template-columns:1fr}}
</style>"""


def esc(text):
    return html.escape(str(text), quote=False)


def attr(text):
    return html.escape(str(text), quote=True)


# ---- block builders (mirrors build_settlements_page.py) --------------------

def p(text, class_name=None):
    open_tag = (f'<!-- wp:paragraph {{"className":"{class_name}"}} -->'
                if class_name else "<!-- wp:paragraph -->")
    cls = f' class="{attr(class_name)}"' if class_name else ""
    return f"{open_tag}\n<p{cls}>{text}</p>\n<!-- /wp:paragraph -->"


def h(level, text):
    return (f'<!-- wp:heading {{"level":{level}}} -->\n'
            f'<h{level} class="wp-block-heading">{text}</h{level}>\n'
            f"<!-- /wp:heading -->")


def ul(items):
    lis = "\n".join(f"<!-- wp:list-item -->\n<li>{it}</li>\n<!-- /wp:list-item -->"
                    for it in items)
    return f"<!-- wp:list -->\n<ul>{lis}</ul>\n<!-- /wp:list -->"


def ol(items):
    lis = "\n".join(f"<!-- wp:list-item -->\n<li>{it}</li>\n<!-- /wp:list-item -->"
                    for it in items)
    return ('<!-- wp:list {"ordered":true} -->\n'
            f"<ol>{lis}</ol>\n<!-- /wp:list -->")


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
    inner = "\n".join(parts)
    return ('<!-- wp:buttons -->\n'
            f'<div class="wp-block-buttons">{inner}</div>\n<!-- /wp:buttons -->')


def group(inner, attrs="", anchor=None, class_name=None):
    open_comment = f"<!-- wp:group {attrs} -->" if attrs else "<!-- wp:group -->"
    div_cls = "wp-block-group" + (f" {class_name}" if class_name else "")
    div_id = f' id="{attr(anchor)}"' if anchor else ""
    return f'{open_comment}\n<div class="{div_cls}"{div_id}>{inner}</div>\n<!-- /wp:group -->'


def html_block(raw):
    return f"<!-- wp:html -->\n{raw}\n<!-- /wp:html -->"


# ---- media -----------------------------------------------------------------

def media_map():
    """exhibit key -> source_url, resolved from the WordPress media library."""
    c = wp_api.client()
    out = {}
    for key, (_cap, filename) in EXHIBITS.items():
        res = c.call("GET", f"/wp/v2/media?search={urllib.parse.quote(filename)}"
                    f"&per_page=5", quiet=True)
        hit = next((m for m in res if m.get("source_url", "").endswith(filename)), None)
        if hit is None:
            raise SystemExit(f"media not found for {filename}")
        out[key] = hit["source_url"]
    return out


# ---- page ------------------------------------------------------------------

def build_blocks(media):
    blocks = [PAGE_CSS]

    # 1. Hero
    stat_cells = []
    for num, lbl in STATS:
        cls = ' class="pdf-stat-num wrd-stat-range"' if len(num) > 8 else \
              ' class="pdf-stat-num"'
        stat_cells.append(
            f'<div class="pdf-stat"><div{cls}>{esc(num)}</div>'
            f'<div class="pdf-stat-lbl">{esc(lbl)}</div></div>')
    stats = ('<div class="pdf-stats"><div class="pdf-stats-grid">'
             + "".join(stat_cells) + "</div></div>")

    hero_inner = "\n".join([
        p("Public records project", class_name="pdf-kicker"),
        h(1, esc(TITLE)),
        p("What a publicly funded DEI Coordinator position was assigned to do, "
          "what the public asked to inspect, what access to those records was "
          "estimated to cost, and how the Supervisor of Records proceedings "
          "handled the dispute."),
        p("On July 31, 2026, Parent Data Force asked Weston Public Schools for "
          "the first three months of work by its Diversity, Equity, and "
          "Inclusion Coordinator. The district answered with a fee estimate of "
          "$5,416.67, and two weeks later said it had run no electronic searches "
          "to build that estimate. Two appeals, two determinations, and a "
          "pending reconsideration followed. No responsive record has been "
          "produced. This project assembles the record from the district’s own "
          "responses and the Supervisor’s decisions."),
        group(p("<strong>What this project evaluates.</strong> This is a project "
                "about how public tax dollars are used for administrative roles, "
                "examined through one publicly funded position as a case study. "
                "The position in view — a Diversity, Equity, and Inclusion "
                "Coordinator — is exclusively dedicated to DEI, which is exactly "
                "what makes it a workable test case: every public dollar behind "
                "it funded work only that role would do. This project is "
                "<strong>not</strong> an evaluation of DEI as a policy question "
                "and takes no position for or against DEI, its methods, or its "
                "conclusions. It asks four narrower questions: what the position "
                "was assigned to do, what it was paid to produce, what it "
                "actually produced, and what it costs the public to find out."),
              class_name="wrd-frame"),
        buttons([
            ("Send us what you have", MAILTO_CONTACT, False),
            ("Read the full article", ARTICLE_URL, True),
            ("All projects", PROJECTS_URL, True),
        ]),
        html_block(stats),
        p(f"Last updated: {UPDATED}", class_name="wrd-updated"),
    ])
    blocks.append(group(hero_inner, attrs='{"align":"wide","className":"wrd-hero"}',
                        class_name="wrd-hero"))

    # 2. What the records establish / do not establish / may reasonably be assumed
    yes = group(h(2, "What the records establish") + "\n" + ul(ESTABLISHED),
                attrs='{"className":"wrd-panel wrd-panel--yes"}',
                class_name="wrd-panel wrd-panel--yes")
    no = group(h(2, "What the records do not establish") + "\n" + ul(NOT_ESTABLISHED),
               attrs='{"className":"wrd-panel wrd-panel--no"}',
               class_name="wrd-panel wrd-panel--no")
    assume = group(h(2, "What can reasonably be assumed pending further records")
                   + "\n"
                   + p("Neither established nor refuted. These are the readings "
                       "the current record supports as the most economical "
                       "explanation of an estimate built without measurement. "
                       "No source states any of them, and none should be cited "
                       "as a finding.")
                   + "\n"
                   + ul(REASONABLY_ASSUMED),
                   attrs='{"className":"wrd-panel wrd-panel--assume"}',
                   class_name="wrd-panel wrd-panel--assume")
    blocks.append(yes)
    blocks.append(no)
    blocks.append(assume)

    # 3. Timeline
    blocks.append(group(h(2, "Timeline") + "\n" + ol(TIMELINE),
                        attrs='{"className":"wrd-timeline"}',
                        class_name="wrd-timeline"))

    # 4. Key records gallery
    figures = []
    for key in sorted(EXHIBITS):
        cap, _fn = EXHIBITS[key]
        figures.append(
            f'<figure><img src="{attr(media[key])}" alt="Exhibit {key}: {attr(cap)}" '
            f'loading="lazy"><figcaption><strong>Exhibit {key}.</strong> '
            f"{esc(cap)}</figcaption></figure>")
    gallery = ('<div class="wrd-gallery"><div class="wrd-gallery-grid">'
               + "".join(figures) + "</div></div>")
    gallery_block = group(h(2, "Key records from the fee dispute")
                          + "\n"
                          + p("Ten unaltered crops of the primary documents: "
                              "the request, the district’s two responses, both "
                              "Supervisor determinations, and the "
                              "acknowledgement of the pending reconsideration. "
                              "The two response PDFs and the two determination "
                              "PDFs are crop sources only and are not published "
                              "as downloads.")
                          + "\n"
                          + html_block(gallery),
                          attrs='{"className":"wrd-gallery-wrap"}',
                          class_name="wrd-gallery")
    blocks.append(gallery_block)

    # 5. Open questions
    blocks.append(group(h(2, "What is still blocked") + "\n"
                        + ul(OPEN_QUESTIONS),
                        attrs='{"className":"wrd-panel"}',
                        class_name="wrd-panel"))

    # 6. Footer CTA
    cta = group(h(2, "Add to this record") + "\n"
                + p("If you hold a record from this matter — a Weston "
                    "response, a determination, a filing, or a copy of "
                    "something the district has since produced — send it to us. "
                    "Corrections to anything published here are welcome, and we "
                    "will report a reconsideration decision as soon as it "
                    "issues.")
                + "\n"
                + buttons([
                    (f"Email {CONTACT}", MAILTO_CONTACT, False),
                    ("Read the full article", ARTICLE_URL, True),
                    ("Donate", DONATE_URL, True),
                ]),
                attrs='{"className":"wrd-cta"}',
                class_name="wrd-cta")
    blocks.append(cta)

    return "\n\n".join(blocks) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--status", choices=("draft", "publish"), default="publish")
    args = ap.parse_args()

    content = build_blocks(media_map())

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
        "exhibits": len(EXHIBITS),
        "content_chars": len(content),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
