#!/usr/bin/env python3
"""Build and idempotently publish the East Bridgewater Public Records Project hub.

Copied from build_weston_page.py: same block helpers, same upsert shape, same
media-library lookup, same print-JSON contract. Stdlib only.

Every `wrd-` class prefix is renamed to `ebw-` so this page cannot inherit
Weston's page-scoped styles. Page CSS references only --pdf-* tokens, so the
Paper and Split style variations keep working.

Usage:
  python build_east_bridgewater_page.py --status draft
  python build_east_bridgewater_page.py --status publish
"""
import argparse
import html
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wp_api

SLUG = "east-bridgewater-public-records-project"
TITLE = "East Bridgewater Public Schools Public Records Project"
PAGE_TEMPLATE = "page-no-title"
CONTACT = "joey@parentdataforce.com"

HUB_URL = "https://www.parentdataforce.com/east-bridgewater-public-records-project/"
ARTICLE_DETERMINATION = ("https://www.parentdataforce.com/"
                         "east-bridgewater-3207-determination/")
ARTICLE_BLACKOUT = ("https://www.parentdataforce.com/"
                    "east-bridgewater-blackout-and-the-missing-february-2025-record/")
ARTICLE_FEE = ("https://www.parentdataforce.com/"
               "east-bridgewater-second-fee-dispute-350-spr-4068-4069/")
ARTICLE_FEE_ORIGINAL = ("https://www.parentdataforce.com/"
                        "east-bridgewater-350-fee-estimate-under-appeal/")
ARTICLE_PETITION = ("https://www.parentdataforce.com/"
                    "two-districts-one-petition-same-words/")
PROJECTS_URL = "https://www.parentdataforce.com/projects/"
DONATE_URL = "https://www.parentdataforce.com/donate/"
MAILTO_CONTACT = (
    "mailto:joey@parentdataforce.com"
    "?subject=East%20Bridgewater%20SPR26%2F3207%20records"
)

UPDATED = "October 1, 2026"

# Exhibit images, uploaded by upload_exhibits.py. Keyed by exhibit number so the
# gallery stays readable; values are the media filenames resolved in the library.
# No student content appears in any exhibit: these are public filings only.
EXHIBITS = {
    "01": ("The determination header: the Commonwealth of Massachusetts Public "
           "Records Division, Manza Arthur, Supervisor of Records, the "
           "August 28, 2026 date, and the docket number SPR26/3207.",
           "east-bridgewater-exhibit-01.png"),
    "02": ("The District’s August 17 position, quoted in full: it does not "
           "possess any additional records, nor is it withholding any records.",
           "east-bridgewater-exhibit-02.png"),
    "03": ("The appeal position as quoted in the determination, including File "
           "12 and its approximately 47 pages of near-total redaction, the known "
           "February 2025 employee record, and apparently omitted responsive "
           "attachments.",
           "east-bridgewater-exhibit-03.png"),
    "04": ("The holding and order: student and parent name redactions upheld, "
           "the remaining redactions not adequately explained, the "
           "missing-record issue resolved procedurally, and a response ordered "
           "within ten business days.",
           "east-bridgewater-exhibit-04.png"),
    "05": ("The District’s September 14, 2026 position on pages 73-119 of File "
           "12: the documents constitute student work in their entirety, were "
           "prepared by students, and cannot be redacted any less.",
           "east-bridgewater-exhibit-05.png"),
}

STATS = [
    ("2,243", "pages produced"),
    ("47", "pages near-total redacted"),
    ("SPR26/3207", "determination, Aug. 28"),
    ("Sept. 14", "District response"),
    ("Sept. 11", "in camera records submitted"),
    ("Pending", "Supervisor's ruling"),
]

DECISION_LINE = "UPHELD IN PART / EXPLAIN MORE"

ISSUES = [
    ("The 47-page blackout",
     "File 12, pages 73 through 119, is described in the July 28, 2026 filing "
     "as almost entirely blacked out: page 73 reveals only part of a student "
     "email header, pages 74 through 119 give essentially no usable information, "
     "and page 120 returns abruptly to unrelated content. The District's own "
     "example for its fourth redaction category was “pages 73-119 of File 12 "
     "contain student assignments.” The Supervisor found the name redactions "
     "adequate and the remaining redactions unclear. On September 14 the "
     "District said those pages are student work in their entirety and cannot be "
     "redacted any less."),
    ("The unreconciled February 2025 record",
     "On June 2, 2026 the District wrote that a letter from an employee to the "
     "School Committee dated February 2025 may have been produced, said it "
     "“should have been withheld and/or redacted,” and asked that it be deleted "
     "and destroyed. The August 28 supplemental submission identified it "
     "precisely: a 31-page February 11, 2025 letter to the School Committee, "
     "embedded in the copy preserved from the District's own production under "
     "the file title “2025-02-11 School Committee letter final PDF.pdf.” The "
     "District's September 14 letter, captioned to SPR26/3207 and SPR26/3203, "
     "does not mention it."),
    ("Attachments shown by name only",
     "The April 27 request asked for complete threads. The July 28 filing "
     "identified attachment filenames appearing in the production without the "
     "attachments themselves — a Staples quote and a classroom-supply list in "
     "File 5, a treasurer's report and an agenda in File 6, and delivery "
     "photographs in Files 9 and 10. No filing after September 14 addresses "
     "them."),
]

TIMELINE = [
    "<strong>April 27, 2026 — the request.</strong> An amended public records "
    "request for all emails sent to or from any district-controlled account in "
    "which the word “stapler” appeared in the subject line or body, covering "
    "April 27, 2023 forward, across the district's known domains and subdomains, "
    "with complete threads including messages that did not themselves contain "
    "the word.",
    "<strong>May 14, 2026 — interim contact.</strong> The District stated it had "
    "located hundreds of potentially responsive emails, asked for an extension to "
    "May 29, and noted the search returned both staff and student emails.",
    "<strong>On or about May 28, 2026 — the first production.</strong> Records "
    "were produced, including email materials and .pst files inside a zip "
    "archive.",
    "<strong>June 2, 2026 — the acknowledgment.</strong> The District wrote that "
    "confidential personnel documents “may have been inadvertently disclosed,” "
    "identified a letter from an employee to the School Committee dated February "
    "2025, said it “should have been withheld and/or redacted,” and asked the "
    "requester to delete and destroy it.",
    "<strong>June 15, 2026 — the written response.</strong> The District cited "
    "Exemption (a) and FERPA, listing four redacted categories, and offered to "
    "mail the documents or make them available for pickup.",
    "<strong>July 27, 2026 — the electronic production.</strong> A secure link "
    "to 13 PDFs totaling <strong>2,243 pages</strong>, File 1 through File 13, "
    "with the June 15 exemptions restated as “remain applicable.”",
    "<strong>July 28, 2026 — the supplemental appeal.</strong> A filing in "
    "SPR26/2791 described the 47-page blackout page by page, identified the "
    "unreconciled February 2025 record and the omitted attachments, and "
    "requested in camera review of the unredacted File 12 pages.",
    "<strong>August 4, 2026 — the first determination.</strong> SPR26/2791 "
    "ordered the School to clarify how the redactions could be withheld under "
    "FERPA through Exemption (a), and to clarify whether any additional records "
    "existed.",
    "<strong>August 17, 2026 — the response that spawned four appeals.</strong> "
    "The School responded. SPR26/3203, SPR26/3207, SPR26/3208 and SPR26/3220 "
    "followed from that single response.",
    "<strong>August 28, 2026 — the determination.</strong> In SPR26/3207 the "
    "Supervisor upheld the redaction of student and parent names under FERPA, "
    "found it unclear how the remaining redactions constitute personally "
    "identifiable information or education records, ordered the School to "
    "clarify, resolved the missing-record issue on procedural grounds, and "
    "ordered a response within ten business days. A supplemental submission "
    "identifying the February 11, 2025 School Committee letter was filed the "
    "same day.",
    "<strong>August 31, 2026 — three companion determinations.</strong> "
    "SPR26/3203 on records responsive to a June 3, 2026 email and its "
    "attachment; SPR26/3208, which <strong>ordered the unredacted records "
    "submitted for in camera inspection</strong>; and SPR26/3220.",
    "<strong>September 11, 2026 — in camera records received.</strong> The "
    "Public Records Division confirmed receipt of records submitted for in "
    "camera review in SPR26/3208 and set a decision due 15 business days from "
    "receipt. The Division does not release in camera records to anyone, so "
    "this is a review, not a disclosure.",
    "<strong>September 14, 2026 — the District's answer.</strong> A letter "
    "captioned RE: SPR26/3207, SPR26/3203, copying the Supervisor, arrived on "
    "the tenth business day after the August 28 order, counting Labor Day as a "
    "state holiday. It defended the pages 73-119 redactions and stated the "
    "District holds no other responsive records “including but not limited to "
    "metadata.”",
    "<strong>September 18, 2026 — a separate dispute begins.</strong> A new "
    "request for student settlement and resolution agreements from September 18, "
    "2021 forward, expressly excluding employment and commercial records and "
    "disclaiming any request for student personally identifiable information.",
    "<strong>September 28–29, 2026 — the fee fight is appealed.</strong> The "
    "District answered the settlement request with a <strong>$350</strong> fee "
    "estimate and a request for 30 more business days, justified by District "
    "Counsel's workload at other districts. The estimate was appealed as "
    "<strong>SPR26/4068</strong> and the time petition as "
    "<strong>SPR26/4069</strong>, both acknowledged September 29. Neither has a "
    "determination.",
]

ESTABLISHED = [
    "East Bridgewater produced 13 PDFs totaling 2,243 pages by secure link on "
    "July 27, 2026, after a partial production on or about May 28–29.",
    "The District invoked Exemption (a) and FERPA, citing four redacted "
    "categories: student names; the names of a student's parent or other family "
    "members; a personal identifier; and information linkable to a specific "
    "student. The District's own worked example was “pages 73-119 of File 12 "
    "contain student assignments.”",
    "The District stated on August 17, 2026 that it does not possess any "
    "additional records and is not withholding any records.",
    "The Supervisor found the School met its burden to redact student names and "
    "the names of a student's parent under FERPA as it operates through "
    "Exemption (a).",
    "The Supervisor found it unclear how the remaining redactions constitute "
    "personally identifiable information or education records, and ordered the "
    "School to clarify the matter.",
    "The Supervisor found the missing-record portion of the appeal resolved on "
    "the ground that this office has no authority to compel the School to create "
    "records.",
    "The School was ordered to respond within ten business days, and the "
    "requester retained a ninety-day right to appeal the substance of that "
    "response.",
    "On September 14, 2026 the District stated the pages 73-119 documents "
    "“constitute student work/assignments in their entirety and were prepared by "
    "students,” and that no lesser redaction is possible without exposing the "
    "District to liability.",
    "The September 14, 2026 letter does not mention the February 11, 2025 "
    "School Committee letter identified in the August 28 supplemental "
    "submission.",
    "On September 11, 2026 the District submitted records for in camera "
    "inspection in SPR26/3208, with a decision due 15 business days from receipt.",
    "On September 28, 2026 the District answered a separate settlement-records "
    "request with an estimate of $350 — five hours of search at $25 and three "
    "hours of review at $75 — and sought 30 additional business days.",
]

NOT_ESTABLISHED = [
    "It is not established that all redactions were improper. The determination "
    "upheld the name redactions and declined to rule on the others. Neither a "
    "clean sweep nor a clean bill.",
    "It is not established that the remaining redactions are lawful. The finding "
    "is that they were not adequately explained, which is narrower than either "
    "upholding or condemning them.",
    "It is not established that a record was withheld. The missing-record issue "
    "was closed procedurally; no one found the District was withholding anything.",
    "It is not established that the District's “no additional records” statement "
    "is accurate. The determination accepted it as the District's position and "
    "explained why the office could not test it.",
    "It is not established that the September 14 letter is correct. It is the "
    "District's assertion, and the Supervisor has not ruled on it.",
    "It is not established that any student record was disclosed unlawfully. The "
    "District asked for the February 2025 letter to be deleted; whether the "
    "original production contained material it lacked authority to release is "
    "contested and undecided.",
    "It is not established that pages 73-119 are the only heavily redacted pages. "
    "The clarification order was general; the September 14 answer was specific.",
    "It is not established what the in camera review will find. Those records "
    "are unreleased by operation of the process that received them.",
    "It is not established why the September 14 letter does not address the "
    "February 2025 record. That is recorded as a question, not answered here.",
    "It is not established that the $350 fee estimate is unreasonable — or that "
    "it is reasonable. Both dockets are pending.",
]

REASONABLY_ASSUMED = [
    "The remaining redactions probably exceed the identity redactions. A district "
    "that had confined itself to names would not have drawn a clarification "
    "order. This is an inference from the shape of the ruling, not a count.",
    "The 47 pages are probably genuinely student work. The District has asserted "
    "this twice in writing and has a privacy interest in being right. That is "
    "not proof, and the Supervisor has not accepted it.",
    "The September 14 letter probably was written to close the clarification "
    "order rather than to open a negotiation. It answers two dockets in one "
    "document, restates the June 15 categories, and then defends the flagged "
    "example. The February 2025 letter may not have been on the checklist.",
    "The February 2025 record probably still exists somewhere in the District's "
    "systems. A district does not ordinarily write to a requester about a "
    "specific document, describe its date and recipient, and ask for its "
    "destruction unless it has identified that document. The District's IT team "
    "was, in its own words, reviewing what had been sent in error.",
    "The 47-page blackout probably spans more than one record. A run crossing the "
    "end of a student email header at page 73 and an abrupt return to a newsletter "
    "at page 120 spans at least a boundary.",
    "The in camera submission probably concerns Exemption (c) and attorney-client "
    "privilege claims rather than FERPA. The SPR26/3208 order concerns the 17 "
    "documents redacted under Exemption (c) and privilege — a separate track from "
    "the File 12 redactions.",
    "The attachments in Files 5, 6, 9 and 10 probably exist. Requesters "
    "routinely see filenames in productions where the attachments were withheld "
    "or overlooked. That pattern is common and proves nothing about these four.",
]

OPEN_QUESTIONS = [
    "No ruling on the September 14 letter. The Supervisor has neither accepted "
    "nor rejected the District's account of pages 73-119.",
    "No ruling on the remaining redactions. The clarification order stands "
    "unanswered as a determination.",
    "The February 11, 2025 School Committee letter is unaddressed in the "
    "September 14 letter. Produced, withheld, inside the blackout, or not located "
    "— none of these has been stated in any filing.",
    "The omitted attachments in Files 5, 6, 9 and 10 are unaddressed since "
    "July 28, 2026.",
    "Whether pages outside 73-119 remain near-total redacted is unknown.",
    "The in camera determination in SPR26/3208 had not issued as of October 1, "
    "2026. The Public Records Division does not release in camera records to "
    "anyone, so a favorable outcome would not itself produce public disclosure.",
    "SPR26/4068 and SPR26/4069, the fee and time dockets, are pending. No "
    "determination on the $350 estimate or the 30-business-day extension.",
    "No responsive document from the September 18, 2026 settlement request has "
    "been released.",
    "Whether an appeal of the September 14 response has been filed. None "
    "appeared in the docket as of October 1, 2026; the determination preserves a "
    "ninety-day window from that response.",
]

PAGE_CSS = """<style>
/* East Bridgewater Public Records Project — page-scoped styles.
   Tokens only, so the Paper and Split variations keep working. */
.ebw-hero{padding-top:2.5rem}
.ebw-updated{margin:.25rem 0 0;color:var(--pdf-mid,#a0a0a0);font-size:.8125rem}
.ebw-frame{border:1px solid var(--pdf-line,#2a2a2a);border-left:3px solid var(--pdf-signal,#ff5a1f);background:var(--pdf-ink-1,#161616);padding:0.9rem 1.1rem;margin:1.5rem 0}
.ebw-frame p{margin:0;font-size:0.95rem;line-height:1.55}
.ebw-decision{border:1px solid var(--pdf-line,#2a2a2a);border-left:3px solid var(--pdf-signal,#ff5a1f);background:var(--pdf-ink-1,#161616);padding:1.25rem;margin:1.5rem 0 0}
.ebw-decision-line{font-size:1.25rem;letter-spacing:.06em;line-height:1.3;color:var(--pdf-signal,#ff5a1f);font-weight:700;margin:0 0 .6rem}
.ebw-decision p{margin:0 0 .6rem;font-size:0.95rem;line-height:1.55}
.ebw-decision p:last-child{margin-bottom:0}
.ebw-decision ul{margin-bottom:0}
.ebw-issue{border:1px solid var(--pdf-line,#2a2a2a);border-top:3px solid var(--pdf-signal,#ff5a1f);background:var(--pdf-ink-1,#161616);padding:1.15rem 1.25rem;margin:1.25rem 0 0}
.ebw-issue h3{margin:0 0 .5rem}
.ebw-issue p{margin:0;font-size:0.95rem;line-height:1.6}
.ebw-panel{border:1px solid var(--pdf-line,#2a2a2a);background:var(--pdf-ink-1,#161616);padding:1.5rem 1.25rem;margin:1.5rem 0 0}
.ebw-panel--yes{border-left:3px solid var(--pdf-signal,#ff5a1f)}
.ebw-panel--no{border-left:3px solid var(--pdf-mid,#a0a0a0)}
.ebw-panel--assume{border-left:3px solid var(--pdf-signal-hi,#ffa366)}
.ebw-panel h2{margin-top:0}
.ebw-panel ul{margin-bottom:0}
.ebw-gallery{border:1px solid var(--pdf-line,#2a2a2a);background:var(--pdf-ink-1,#161616);padding:1.25rem;margin:1.5rem 0 0}
.ebw-gallery-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.25rem;margin:0}
.ebw-gallery-grid figure{margin:0}
.ebw-gallery-grid img{width:100%;height:auto;border:1px solid var(--pdf-line,#2a2a2a);border-radius:4px;background:#fff}
.ebw-gallery-grid figcaption{font-size:.8125rem;color:var(--pdf-mid,#a0a0a0);margin-top:.4rem;line-height:1.45}
.ebw-timeline{border:1px solid var(--pdf-line,#2a2a2a);background:var(--pdf-ink-1,#161616);padding:1.5rem 1.25rem;margin:1.5rem 0 0}
.ebw-timeline li{margin-bottom:.85rem}
.ebw-timeline li:last-child{margin-bottom:0}
.ebw-stat-range{font-size:1.125rem;letter-spacing:.01em;line-height:1.25;padding-top:.45rem}
.ebw-cta{border:1px solid var(--pdf-line,#2a2a2a);background:var(--pdf-ink-1,#161616);padding:1.5rem;margin:1.5rem 0 0}
@media (max-width:719px){.ebw-gallery-grid{grid-template-columns:1fr}}
</style>"""


def esc(text):
    return html.escape(str(text), quote=False)


def attr(text):
    return html.escape(str(text), quote=True)


# ---- block builders (mirrors build_weston_page.py) ------------------------

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
        cls = ' class="pdf-stat-num ebw-stat-range"' if len(num) > 8 else \
              ' class="pdf-stat-num"'
        stat_cells.append(
            f'<div class="pdf-stat"><div{cls}>{esc(num)}</div>'
            f'<div class="pdf-stat-lbl">{esc(lbl)}</div></div>')
    stats = ('<div class="pdf-stats"><div class="pdf-stats-grid">'
             + "".join(stat_cells) + "</div></div>")

    hero_inner = "\n".join([
        p("Public records project", class_name="pdf-kicker"),
        h(1, esc(TITLE)),
        p("Thirteen PDFs, 2,243 pages of district email, a 47-page blackout in "
          "the middle of one of them, and a 31-page School Committee letter the "
          "District says it does not have. What the Supervisor of Records "
          "decided, what it did not decide, and what is still open."),
        p("On April 27, 2026, Parent Data Force asked East Bridgewater Public "
          "Schools for every email containing the word “stapler.” The District "
          "produced 13 PDFs totaling 2,243 pages. A state supervisor then "
          "upheld some of the redactions, refused to accept the rest, and "
          "closed the question of a missing record without deciding whether that "
          "record existed. Fourteen months of production, and the dispute got "
          "narrower rather than wider. This project assembles the record from "
          "the District's own responses, the Supervisor's decisions, and the "
          "filings on both sides."),
        group(p("<strong>What this project evaluates.</strong> Whether a large "
                "public-records production actually answers a specific, "
                "itemized question — and what happens when a district says the "
                "remaining records do not exist. It examines three things "
                "separately: a 47-page redaction, a single identified document, "
                "and a set of attachments that appear by filename only. "
                "This project is <strong>not</strong> an accusation that "
                "East Bridgewater withheld records unlawfully, and it takes no "
                "position on the redactions as a whole. Two of those questions "
                "are live and undecided. Where the record is silent, this page "
                "says so rather than filling the gap."),
              class_name="ebw-frame"),
        buttons([
            ("Send us what you have", MAILTO_CONTACT, False),
            ("Read the determination", ARTICLE_DETERMINATION, True),
            ("All projects", PROJECTS_URL, True),
        ]),
        html_block(stats),
        p(f"Last updated: {UPDATED}", class_name="ebw-updated"),
    ])
    blocks.append(group(hero_inner, attrs='{"align":"wide","className":"ebw-hero"}',
                        class_name="ebw-hero"))

    # 2. What the Supervisor decided
    decision = group(
        p(esc(DECISION_LINE), class_name="ebw-decision-line")
        + "\n"
        + p("The August 28, 2026 determination in <strong>SPR26/3207</strong> "
            "resolved three questions and left a fourth open. The framing "
            "matters more than the headline, because a determination that "
            "upholds some redactions is not a determination that the production "
            "was lawful.")
        + "\n"
        + ul([
            "<strong>Upheld.</strong> Where the School redacted student names "
            "and the names of a student's parent under FERPA as it operates "
            "through Exemption (a), the Supervisor found “the School has met its "
            "burden to redact such information.”",
            "<strong>Not upheld, and not condemned.</strong> As to the remaining "
            "redactions, “it is unclear how the remaining redactions constitute "
            "personally identifiable information or education records.” The "
            "School “must further clarify this matter.”",
            "<strong>Resolved procedurally.</strong> On the missing-record "
            "question, because the District stated it holds nothing further and "
            "“this office has no authority to compel the School to create "
            "records,” the Supervisor found that portion of the appeal "
            "“resolved.” That is not a finding that no record was withheld.",
            "<strong>Still open.</strong> The School was ordered to respond "
            "within ten business days. It did so on September 14, 2026. The "
            "Supervisor has not ruled on that response.",
        ]),
        attrs='{"className":"ebw-decision"}',
        class_name="ebw-decision")
    blocks.append(decision)

    # 3. The three open issues
    issue_blocks = [h(2, "The three open issues")]
    for title, body in ISSUES:
        issue_blocks.append(
            group(h(3, esc(title)) + "\n" + p(esc(body)),
                  attrs='{"className":"ebw-issue"}',
                  class_name="ebw-issue"))
    blocks.append(group("\n".join(issue_blocks),
                        attrs='{"className":"ebw-panel"}',
                        class_name="ebw-panel"))

    # 4. Established / not established / reasonably assumed
    yes = group(h(2, "What the records establish") + "\n" + ul(ESTABLISHED),
                attrs='{"className":"ebw-panel ebw-panel--yes"}',
                class_name="ebw-panel ebw-panel--yes")
    no = group(h(2, "What the records do not establish") + "\n" + ul(NOT_ESTABLISHED),
               attrs='{"className":"ebw-panel ebw-panel--no"}',
               class_name="ebw-panel ebw-panel--no")
    assume = group(h(2, "What can reasonably be assumed pending further records")
                   + "\n"
                   + p("Neither established nor refuted. These are the readings "
                       "the current record supports as the most economical "
                       "explanation of what is in front of us. No source states "
                       "any of them, and none should be cited as a finding.")
                   + "\n"
                   + ul(REASONABLY_ASSUMED),
                   attrs='{"className":"ebw-panel ebw-panel--assume"}',
                   class_name="ebw-panel ebw-panel--assume")
    blocks.append(yes)
    blocks.append(no)
    blocks.append(assume)

    # 5. Timeline
    blocks.append(group(h(2, "Timeline") + "\n" + ol(TIMELINE),
                        attrs='{"className":"ebw-timeline"}',
                        class_name="ebw-timeline"))

    # 6. Key records gallery
    figures = []
    for key in sorted(EXHIBITS):
        cap, _fn = EXHIBITS[key]
        figures.append(
            f'<figure><img src="{attr(media[key])}" alt="Exhibit {key}: {attr(cap)}" '
            f'loading="lazy"><figcaption><strong>Exhibit {key}.</strong> '
            f"{esc(cap)}</figcaption></figure>")
    gallery = ('<div class="ebw-gallery"><div class="ebw-gallery-grid">'
               + "".join(figures) + "</div></div>")
    gallery_block = group(h(2, "Key records from the appeal")
                          + "\n"
                          + p("Five unaltered crops of public filings: the "
                              "determination header, the District's quoted "
                              "August 17 position, the appeal position as "
                              "quoted, the holding and order, and the District's "
                              "September 14 response. The determination and "
                              "response PDFs are crop sources only and are not "
                              "published as downloads. "
                              "<strong>No page of the 2,243-page production is "
                              "reproduced here.</strong> The material in dispute "
                              "is student work, student communications, and "
                              "personnel correspondence, and a records-disputes "
                              "page that illustrates itself with the records in "
                              "dispute is not a records-disputes page.")
                          + "\n"
                          + html_block(gallery),
                          attrs='{"className":"ebw-gallery-wrap"}',
                          class_name="ebw-gallery")
    blocks.append(gallery_block)

    # 7. Open questions
    blocks.append(group(h(2, "What is still blocked") + "\n"
                        + ul(OPEN_QUESTIONS),
                        attrs='{"className":"ebw-panel"}',
                        class_name="ebw-panel"))

    # 8. Articles in this project
    article_items = [
        f'<strong><a href="{attr(ARTICLE_DETERMINATION)}">What the Supervisor of '
        f"Records Decided About East Bridgewater</a></strong> — the August 28 "
        f"determination itself: what it held, what it sent back, and what "
        f"“resolved” does not mean.",
        f'<strong><a href="{attr(ARTICLE_BLACKOUT)}">East Bridgewater’s 47-Page '
        f"Blackout and the Record It Says It Does Not Have</a></strong> — pages "
        f"73 through 119, the unreconciled February 2025 School Committee "
        f"letter, and the attachments that appear by filename only.",
        f'<strong><a href="{attr(ARTICLE_FEE)}">East Bridgewater’s Second Fee '
        f"Dispute</a></strong> — the September 18, 2026 settlement-records "
        f"request, the $350 estimate, and dockets SPR26/4068 and SPR26/4069. A "
        f"separate fight from the redaction appeal, sharing a district and "
        f"nothing else.",
    ]
    earlier = [
        f'<a href="{attr(ARTICLE_FEE_ORIGINAL)}">East Bridgewater’s $350 Fee and '
        f"30-Day Extension Are Now Under Appeal</a> — the original report on the "
        f"fee dispute.",
        f'<a href="{attr(ARTICLE_PETITION)}">Two Districts, One Petition</a> — '
        f"the shared petition language, alongside Natick.",
    ]
    blocks.append(group(h(2, "Articles in this project") + "\n"
                        + ul(article_items)
                        + "\n"
                        + p("<strong>Earlier reporting on the separate fee "
                            "matter:</strong>")
                        + "\n"
                        + ul(earlier),
                        attrs='{"className":"ebw-panel"}',
                        class_name="ebw-panel"))

    # 9. Footer CTA
    cta = group(h(2, "Add to this record") + "\n"
                + p("If you hold a record from this matter — an East Bridgewater "
                    "response, a determination, a filing, a copy of the "
                    "February 11, 2025 School Committee letter, or an "
                    "attachment from Files 5, 6, 9 or 10 of the production — send "
                    "it to us. The District's position is that it holds no "
                    "further responsive records. If that is wrong, the record "
                    "should say so. Corrections to anything published here are "
                    "welcome, and we will report the Supervisor's rulings as soon "
                    "as they issue.")
                + "\n"
                + buttons([
                    (f"Email {CONTACT}", MAILTO_CONTACT, False),
                    ("Read the determination", ARTICLE_DETERMINATION, True),
                    ("Donate", DONATE_URL, True),
                ]),
                attrs='{"className":"ebw-cta"}',
                class_name="ebw-cta")
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
