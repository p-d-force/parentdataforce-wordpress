#!/usr/bin/env python3
"""Build and idempotently publish the Middleborough Principal-Hiring Records hub.

Mirrors build_weston_page.py: same block helpers (p, h, ul, ol, buttons, group,
html_block used verbatim), same upsert shape, same media-library lookup, same
print-JSON contract. Every `wrd-` class prefix is renamed to `mbr-` so the page
cannot inherit Weston's scoped styles, and page CSS references only `--pdf-*`
tokens so the Paper and Split style variations keep working. Stdlib only.

The successful candidate is anonymized throughout: the Supervisor of Records
uses "[an identified individual]" and the district still withholds the identity.
No string in this file carries the candidate's surname.

Usage:
  python build_middleborough_page.py --status draft
  python build_middleborough_page.py --status publish
"""
import argparse
import html
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wp_api

SLUG = "middleborough-principal-hiring-records-project"
TITLE = "Middleborough Principal-Hiring Records Project"
PAGE_TEMPLATE = "page-no-title"
CONTACT = "joey@parentdataforce.com"

ARTICLE_URL = ("https://www.parentdataforce.com/"
               "middleborough-principal-hiring-records-prr-26-450/")
PROJECTS_URL = "https://www.parentdataforce.com/projects/"
DONATE_URL = "https://www.parentdataforce.com/donate/"
MAILTO_CONTACT = (
    "mailto:joey@parentdataforce.com"
    "?subject=Middleborough%20principal%20hiring%20records"
)

UPDATED = "October 1, 2026"

# Exhibit images, uploaded by upload_exhibits.py. Keyed by exhibit number so the
# gallery stays readable; values are the media filenames resolved in the library.
EXHIBITS = {
    "01": ("The ten categories of records the August 10, 2026 request sought, as "
           "the Supervisor of Records recorded them in the September 8, 2026 "
           "determination.",
           "middleborough-exhibit-01.png"),
    "02": ("The district's August 24, 2026 response letter: responsive records "
           "for items 1 through 7 are included, and there are no responsive "
           "records on file for items 8, 9 and 10.",
           "middleborough-exhibit-02.png"),
    "03": ("The September 8, 2026 determination on the successful candidate's "
           "personal information: a personal cell phone number and email were "
           "upheld, the address was not justified under the privacy clause of "
           "Exemption (c).",
           "middleborough-exhibit-03.png"),
    "04": ("The September 8, 2026 determination on the twenty-four unsuccessful "
           "applicants: the School had not met its burden to withhold entirely "
           "their individualized information, applying the finalist analysis "
           "from Attorney General v. School Committee of Northampton.",
           "middleborough-exhibit-04.png"),
    "05": ("The September 22, 2026 determination in SPR26/3602, applying the "
           "same finalist analysis to the same principal search: the School had "
           "not met its burden to redact the identifying information of "
           "candidates who were not hired.",
           "middleborough-exhibit-05.png"),
    "06": ("G.L. c. 66, § 3A, quoted in full in the September 29, 2026 "
           "reconsideration determination: recommendations submitted in support "
           "of candidates who are hired, for the position to which they apply, "
           "are public records.",
           "middleborough-exhibit-06.png"),
    "07": ("The September 29, 2026 determination: the School must confirm that "
           "any withheld portions of the referenced records do not constitute "
           "public records under G.L. c. 66, § 3A.",
           "middleborough-exhibit-07.png"),
    "08": ("The district's September 4, 2026 response to the supplemental "
           "request, item 3: it withheld and continues to withhold responsive "
           "records relating to the other applicants, including the other "
           "finalist, on privacy grounds.",
           "middleborough-exhibit-08.png"),
}

STATS = [
    ("August 10, 2026", "request filed"),
    ("53 pages", "first production"),
    ("24", "unsuccessful applicants withheld"),
    ("Sept 8", "Supervisor finds burden unmet"),
    ("3 dockets", "one still open"),
    ("Pending", "district's response due"),
]

TIMELINE = [
    "<strong>August 10, 2026 — the request.</strong> Parent Data Force filed a "
    "public-records request with Middleborough Public Schools through the "
    "NextRequest portal, logged as PRR #26-450. Ten enumerated categories "
    "covering the recruitment, evaluation, selection, appointment and "
    "compensation of the successful candidate, with express exclusions for "
    "private material and permission to anonymize unsuccessful applicants.",
    "<strong>August 24, 2026 — the production.</strong> The district produced "
    "fifty-three pages responsive to items 1 through 7, redacted under "
    "Exemption (c), and stated there were <strong>no responsive records on file "
    "for items 8, 9 and 10</strong> — internal communications, search and audit "
    "logs, and native electronic production.",
    "<strong>August 25, 2026 — the appeal.</strong> Parent Data Force appealed "
    "under G.L. c. 66, § 10A, arguing the Exemption (c) explanation was too "
    "categorical to satisfy the specificity requirement and that the production "
    "was incomplete. The appeal was assigned docket <strong>SPR26/3331</strong>.",
    "<strong>August 25, 2026 — the supplemental request.</strong> A separate "
    "request sought the records of the $142,000 salary, the offer and contract "
    "transmittal, the finalist-selection materials, the July 29 notation, the "
    "Fall River communication, and the reference-call notes.",
    "<strong>September 4, 2026 — the second response.</strong> The district "
    "answered the supplemental request, produced some material, and stated for "
    "items 1, 2, 3, 5 and 6 that it had no additional responsive records. It "
    "withheld and <strong>continues to withhold</strong> records relating to the "
    "other applicants, <strong>including the other finalist</strong>, and it "
    "corrected its applicant count from twenty-five to thirty.",
    "<strong>September 5, 2026 — the SPR26/3602 appeal.</strong> Parent Data "
    "Force appealed the September 4 response rather than folding it into "
    "SPR26/3331. It was assigned docket <strong>SPR26/3602</strong>.",
    "<strong>September 8, 2026 — the first determination.</strong> The Supervisor "
    "upheld the redaction of grades earned and analysis of interview responses "
    "under the personnel clause of Exemption (c), and upheld a personal phone "
    "number and email under the privacy clause. The Supervisor found it "
    "<strong>unclear how the School may redact the address</strong> under the "
    "privacy clause, and that the School <strong>had not met its burden to "
    "withhold entirely</strong> the individualized information about the "
    "twenty-four unsuccessful applicants.",
    "<strong>September 8, 2026 — the § 3A reconsideration request.</strong> "
    "Parent Data Force requested narrow reconsideration of one question: whether "
    "the approval of redactions to <em>details relating to recommendations "
    "received</em> was intended to authorize withholding external "
    "recommendations for the candidate who was ultimately hired.",
    "<strong>September 9, 2026 — reconsideration opened.</strong> The Public "
    "Records Division opened reconsideration in SPR26/3331.",
    "<strong>September 22, 2026 — the SPR26/3602 determination.</strong> The "
    "Supervisor found the School had <strong>not met its burden to redact the "
    "identifying information of the candidates who were not hired</strong>, "
    "reapplied the finalist analysis to this same search, held that "
    "<em>unresponsive</em> is not an exemption, and ordered a response within "
    "ten business days.",
    "<strong>September 22, 2026 — the district's response.</strong> The district "
    "answered SPR26/3331 and <strong>confirmed that the person whose identity it "
    "withholds is the finalist who was not appointed</strong>, arguing that the "
    "Northampton finalist analysis does not carry over from a superintendent "
    "search to a principal search. A corrected copy was sent that night.",
    "<strong>September 22, 2026 — the third appeal.</strong> Parent Data Force "
    "appealed that response, opening docket <strong>SPR26/3939</strong>, which "
    "remains open and undetermined.",
    "<strong>September 23, 2026 — supplemental submission.</strong> A filing put "
    "the SPR26/3602 finalist holding before SPR26/3939, arguing that the "
    "Supervisor applied the governing finalist and privacy framework to this "
    "same search, and that the district has now supplied the fact that was "
    "previously missing: that the withheld person reached finalist stage.",
    "<strong>September 23, 2026 — a letter to district counsel.</strong> A "
    "separate letter asked whether the September 22 determination in SPR26/3602 "
    "changes the district's position on withholding the unsuccessful "
    "finalist's identity, given the district's own confirmation of finalist "
    "status. It remains unanswered in the record.",
    "<strong>September 29, 2026 — the reconsideration determination.</strong> The "
    "Supervisor quoted <strong>G.L. c. 66, § 3A in full</strong> — "
    "recommendations submitted in support of candidates who are hired, for the "
    "position to which they apply, <em>shall be considered public records</em> — "
    "and ordered the School to <strong>confirm that its withheld recommendation "
    "material is not § 3A public records</strong>, within ten business days.",
]

ESTABLISHED = [
    "Parent Data Force requested the records of the Middleborough Public Schools "
    "elementary principal search on August 10, 2026, in ten enumerated "
    "categories, with express exclusions for private material.",
    "The district produced fifty-three pages on August 24, 2026, redacted under "
    "Exemption (c), and stated that <strong>no responsive records were on file "
    "for items 8, 9 and 10</strong> — internal communications, search and audit "
    "logs, and native electronic production.",
    "On September 8, 2026 the Supervisor of Records found the district had "
    "<strong>not met its burden to redact the successful candidate's address</ "
    "strong> under the privacy clause of Exemption (c).",
    "The same determination found the district had <strong>not met its burden "
    "to withhold entirely the individualized information about the "
    "twenty-four unsuccessful applicants</strong>, drawing on the finalist "
    "analysis in <em>Attorney General v. School Committee of Northampton</em>.",
    "On September 22, 2026 the Supervisor applied the same finalist analysis to "
    "the same search in <strong>SPR26/3602</strong> and again found the burden "
    "unmet. The determination also held that <em>unresponsive</em> is not an "
    "exemption.",
    "On September 29, 2026 the Supervisor quoted <strong>G.L. c. 66, § 3A in "
    "full</strong> and ordered the district to confirm that its withheld "
    "recommendation material is not a § 3A public record, within ten business "
    "days.",
    "The district's own September 22, 2026 response confirms that the person "
    "whose identity it continues to withhold is <strong>the other "
    "finalist</strong>.",
    "The Supervisor <strong>upheld</strong> the district's redaction of grades "
    "earned and analysis of interview responses under the personnel clause of "
    "Exemption (c), and of a personal phone number and email under the privacy "
    "clause.",
    "Nothing has been produced under either order. All three determinations "
    "ordered a response within ten business days; none ordered production.",
]

NOT_ESTABLISHED = [
    "It is not established that the address will be released. The Supervisor "
    "found the redaction unjustified <em>as articulated</em>; the district has "
    "not yet explained why it is justified, and may yet.",
    "It is not established that the applicant-pool records will be released in "
    "any particular form.",
    "It is not established that the district's search was incomplete. The "
    "Supervisor found the additional-records question unclear and ordered "
    "clarification. She has not found that records are missing.",
    "It is not established that the recommendation letters are § 3A records. "
    "The Supervisor has required the district to <em>confirm</em> one way or the "
    "other; the district's § 3A response is not in the record.",
    "It is not established that the district's principal-versus-superintendent "
    "distinction fails. It is the district's argument, and no determination has "
    "sustained or rejected it.",
    "The successful candidate's identity is <strong>not public</strong>. The "
    "Supervisor anonymizes him as <em>[an identified individual]</em> and the "
    "district still withholds him.",
    "It is not established anything about whether the right candidate was "
    "hired. That question is not before the Supervisor and is not this "
    "project's subject.",
    "This project takes no position on DEI, on hiring criteria, or on the "
    "merits of the hiring decision.",
]

OPEN_QUESTIONS = [
    "The district's <strong>§ 3A response</strong>, due within ten business "
    "days of September 29, 2026. It must confirm on the record that its "
    "withheld recommendation material is not a § 3A public record.",
    "Any <strong>determination in SPR26/3939</strong>, opened September 22, "
    "2026 and undetermined.",
    "Whether the <strong>address and applicant-pool records</strong> are "
    "released, and in what form.",
    "Whether the district will <strong>identify the applicants who advanced "
    "past initial screening</strong> — the specific fact the Supervisor said it "
    "needed on September 8 and again on September 22.",
    "Whether the <strong>Fall River communication</strong> described in the "
    "production is ever produced, and whether the redacted handwritten "
    "<em>Superintendent notes on references</em> are segregated rather than "
    "withheld whole.",
    "Whether the <strong>successful candidate's identity</strong> is released, "
    "which now turns on a district that has itself confirmed finalist status.",
]

PAGE_CSS = """<style>
/* Middleborough Principal-Hiring Records Project — page-scoped styles.
   Tokens only, so the Paper and Split variations keep working. */
.mbr-hero{padding-top:2.5rem}
.mbr-updated{margin:.25rem 0 0;color:var(--pdf-mid,#a0a0a0);font-size:.8125rem}
.mbr-frame{border:1px solid var(--pdf-line,#2a2a2a);border-left:3px solid var(--pdf-signal,#ff5a1f);background:var(--pdf-ink-1,#161616);padding:0.9rem 1.1rem;margin:1.5rem 0}
.mbr-frame p{margin:0;font-size:0.95rem;line-height:1.55}
.mbr-panel{border:1px solid var(--pdf-line,#2a2a2a);background:var(--pdf-ink-1,#161616);padding:1.5rem 1.25rem;margin:1.5rem 0 0}
.mbr-panel--yes{border-left:3px solid var(--pdf-signal,#ff5a1f)}
.mbr-panel--no{border-left:3px solid var(--pdf-mid,#a0a0a0)}
.mbr-panel--open{border-left:3px solid var(--pdf-signal-hi,#ffa366)}
.mbr-panel h2{margin-top:0}
.mbr-panel ul{margin-bottom:0}
.mbr-gallery{border:1px solid var(--pdf-line,#2a2a2a);background:var(--pdf-ink-1,#161616);padding:1.25rem;margin:1.5rem 0 0}
.mbr-gallery-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.25rem;margin:0}
.mbr-gallery-grid figure{margin:0}
.mbr-gallery-grid img{width:100%;height:auto;border:1px solid var(--pdf-line,#2a2a2a);border-radius:4px;background:#fff}
.mbr-gallery-grid figcaption{font-size:.8125rem;color:var(--pdf-mid,#a0a0a0);margin-top:.4rem;line-height:1.45}
.mbr-timeline{border:1px solid var(--pdf-line,#2a2a2a);background:var(--pdf-ink-1,#161616);padding:1.5rem 1.25rem;margin:1.5rem 0 0}
.mbr-timeline li{margin-bottom:.85rem}
.mbr-timeline li:last-child{margin-bottom:0}
.mbr-stat-range{font-size:1.125rem;letter-spacing:.01em;line-height:1.25;padding-top:.45rem}
.mbr-cta{border:1px solid var(--pdf-line,#2a2a2a);background:var(--pdf-ink-1,#161616);padding:1.5rem;margin:1.5rem 0 0}
@media (max-width:719px){.mbr-gallery-grid{grid-template-columns:1fr}}
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
        cls = ' class="pdf-stat-num mbr-stat-range"' if len(num) > 8 else \
              ' class="pdf-stat-num"'
        stat_cells.append(
            f'<div class="pdf-stat"><div{cls}>{esc(num)}</div>'
            f'<div class="pdf-stat-lbl">{esc(lbl)}</div></div>')
    stats = ('<div class="pdf-stats"><div class="pdf-stats-grid">'
             + "".join(stat_cells) + "</div></div>")

    hero_inner = "\n".join([
        p("Public records project", class_name="pdf-kicker"),
        h(1, esc(TITLE)),
        p("What the public asked to inspect about a publicly funded principal "
          "search, what the district produced, what it said it had no records "
          "of, and how the Supervisor of Records handled the dispute."),
        p("On August 10, 2026, Parent Data Force asked Middleborough Public "
          "Schools for the records of its search to hire a principal at the "
          "Mary K. Goode Elementary School. The district produced fifty-three "
          "pages, said it had no records at all for three of the ten things "
          "asked, and withheld almost everything about the twenty-four people "
          "who applied and did not get the job. Twice, the Supervisor of "
          "Records has held that the district had not met its burden to "
          "redact. On September 29, the Supervisor quoted a statute the "
          "district has not yet answered. This project assembles the record "
          "from the district's own responses and the Supervisor's decisions."),
        group(p("<strong>What this project evaluates.</strong> This is a public-"
                "records project about whether the public can inspect how a "
                "publicly funded administrative decision was made, examined "
                "through one principal search as a case study. The position and "
                "the process are not the subject. This project takes "
                "<strong>no position</strong> on who should have been hired, and "
                "none is implied. It asks narrower questions: what was asked "
                "for, what was produced, what was withheld and on what stated "
                "ground, and whether the custodian carried the burden the law "
                "puts on it."),
              class_name="mbr-frame"),
        group(p("<strong>On the successful candidate's name.</strong> The "
                "Supervisor of Records anonymizes the successful candidate "
                "throughout as <em>[an identified individual]</em>, and "
                "Middleborough Public Schools continues to withhold that "
                "identity. The district's own September 22, 2026 response "
                "confirmed that the withheld person is the other finalist, and "
                "Parent Data Force has asked the district's counsel to "
                "reconsider. <strong>This project does not publish that "
                "identity</strong>, and no document published here carries it. "
                "Where this page says <em>the successful candidate</em>, it "
                "means the person the Supervisor means."),
              class_name="mbr-frame"),
        buttons([
            ("Send us what you have", MAILTO_CONTACT, False),
            ("Read the full article", ARTICLE_URL, True),
            ("All projects", PROJECTS_URL, True),
        ]),
        html_block(stats),
        p(f"Last updated: {UPDATED}", class_name="mbr-updated"),
    ])
    blocks.append(group(hero_inner, attrs='{"align":"wide","className":"mbr-hero"}',
                        class_name="mbr-hero"))

    # 2. What the record establishes / does not establish / remains open
    yes = group(h(2, "What the record establishes") + "\n" + ul(ESTABLISHED),
                attrs='{"className":"mbr-panel mbr-panel--yes"}',
                class_name="mbr-panel mbr-panel--yes")
    no = group(h(2, "What the record does not establish") + "\n" + ul(NOT_ESTABLISHED),
               attrs='{"className":"mbr-panel mbr-panel--no"}',
               class_name="mbr-panel mbr-panel--no")
    openq = group(h(2, "What remains open") + "\n"
                  + p("The three determinations issued so far are clarification "
                      "and response orders, not disclosure orders. Each gave "
                      "the district ten business days to answer. None of those "
                      "answers is in the record as of this writing.")
                  + "\n"
                  + ul(OPEN_QUESTIONS),
                  attrs='{"className":"mbr-panel mbr-panel--open"}',
                  class_name="mbr-panel mbr-panel--open")
    blocks.append(yes)
    blocks.append(no)
    blocks.append(openq)

    # 3. Timeline
    blocks.append(group(h(2, "Timeline") + "\n" + ol(TIMELINE),
                        attrs='{"className":"mbr-timeline"}',
                        class_name="mbr-timeline"))

    # 4. Key records gallery
    figures = []
    for key in sorted(EXHIBITS):
        cap, _fn = EXHIBITS[key]
        figures.append(
            f'<figure><img src="{attr(media[key])}" alt="Exhibit {key}: {attr(cap)}" '
            f'loading="lazy"><figcaption><strong>Exhibit {key}.</strong> '
            f"{esc(cap)}</figcaption></figure>")
    gallery = ('<div class="mbr-gallery"><div class="mbr-gallery-grid">'
               + "".join(figures) + "</div></div>")
    gallery_block = group(h(2, "Key records from the search")
                          + "\n"
                          + p("Eight unaltered crops of the primary documents: "
                              "the ten request categories, both district "
                              "response letters, and the three Supervisor "
                              "determinations. The three determination PDFs and "
                              "the two response-letter PDFs are crop sources "
                              "only and are not published as downloads.")
                          + "\n"
                          + html_block(gallery),
                          attrs='{"className":"mbr-gallery-wrap"}',
                          class_name="mbr-gallery")
    blocks.append(gallery_block)

    # 5. Footer CTA
    cta = group(h(2, "Add to this record") + "\n"
                + p("If you hold a record from this matter — a district "
                    "response, a determination, a filing, or a copy of "
                    "something the district has since produced — send it to us. "
                    "Corrections to anything published here are welcome, and we "
                    "will report the district's § 3A response and any SPR26/3939 "
                    "determination as soon as they issue.")
                + "\n"
                + buttons([
                    (f"Email {CONTACT}", MAILTO_CONTACT, False),
                    ("Read the full article", ARTICLE_URL, True),
                    ("Donate", DONATE_URL, True),
                ]),
                attrs='{"className":"mbr-cta"}',
                class_name="mbr-cta")
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
