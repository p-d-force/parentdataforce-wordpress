#!/usr/bin/env python3
"""Build and idempotently publish the Worcester Cybersecurity Records Project hub.

Mirrors tools/build_settlements_page.py: stdlib only, same block helpers, same
upsert shape. Content is fixed in this file so it can be re-run when the
October 12, 2026 production lands.

Usage:
  python build_worcester_page.py --status draft
  python build_worcester_page.py --status publish
"""
import argparse
import html
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wp_api

SLUG = "worcester-cybersecurity-records-project"
TITLE = "Worcester Cybersecurity Records Project"
PAGE_TEMPLATE = "page-no-title"
CONTACT = "joey@parentdataforce.com"

ARTICLE_URL = "https://www.parentdataforce.com/worcester-phishing-118-pages-of-records/"
PROJECTS_URL = "https://www.parentdataforce.com/projects/"
DONATE_URL = "https://www.parentdataforce.com/donate/"
MAILTO_CONTACT = (
    "mailto:joey@parentdataforce.com"
    "?subject=Worcester%20July%2030%20phishing%20incident"
)

UPDATED = "October 1, 2026"

# Exhibit images, uploaded by the project build. Keyed by exhibit number so the
# gallery stays readable; values are the media source_urls.
EXHIBITS = {
    "66": ("Page 66 — Paul Johnson’s reaction in the “SECURE EMAIL from Tammy "
           "Murray” thread.",
           "worcester-exhibit-23-jean-pray-p66-paul-johnson-reaction.png"),
    "68": ("Page 68 — Jean Pray’s “Thank you!” in the secure-email thread.",
           "worcester-exhibit-24-jean-pray-p68-jean-pray-thank-you.png"),
    "69": ("Page 69 — Jean Pray to Tammy Murray, “Important Update Re: Advocate "
           "Email/Phone Calls.”",
           "worcester-exhibit-19-jean-pray-p69-important-update-advocate-calls.png"),
    "71": ("Page 71 — Paul Johnson’s password-reset response.",
           "worcester-exhibit-18-jean-pray-p71-password-reset-response.png"),
    "72": ("Page 72 — Jean Pray reports broad BCC distribution of the secure "
           "email.",
           "worcester-exhibit-17-jean-pray-p72-secure-email-bcc-distribution.png"),
    "76": ("Page 76 — a rendered copy of the phishing email itself.",
           "worcester-exhibit-01-jean-pray-p76-phishing-email-copy.png"),
    "87": ("Page 87 — Deanna Carlson’s reply in the “Important Update” thread.",
           "worcester-exhibit-25-jean-pray-p87-deanna-carlson-reply.png"),
    "104": ("Page 104 — Deanna Carlson’s reply to attorney Paige Tobin.",
            "worcester-exhibit-26-jean-pray-p104-deanna-carlson-tobin-reply.png"),
    "agenda": ("The official August 13 School Committee agenda, item c&p 6-13.",
               "worcester-exhibit-09-august-13-agenda-c-and-p-6-13.png"),
}

STATS = [
    ("July 30, 2026", "phishing incident"),
    ("10:37 AM", "records request filed"),
    ("SPR26/3372", "appeal docket"),
    ("118 pages", "second-search production"),
    ("Oct 12, 2026", "next production (~594 pages)"),
]

TIMELINE = [
    "<strong>July 30, 2026 — incident.</strong> A message subject "
    "“Worcester Public Schools,” sent under Dr. Tammy Murray’s district "
    "address, offered a “secure message” hosted at "
    "murraytammy.netlify.app. Gmail recorded SPF, DKIM and DMARC passes for "
    "worcesterschools.net, and an independently recomputed DKIM body hash "
    "matched the signed body. This establishes an authenticated "
    "Worcester-authorized sending path; it does not identify who used it.",
    "<strong>July 30, 8:35–8:43 a.m. — technical response.</strong> "
    "Worcester’s Google Workspace audit shows an investigation created at "
    "8:39:46 a.m., content accessed at 8:41:05 with the justification "
    "“phishing investigation,” and a bulk deletion completing at 8:43:37 a.m. "
    "— 581 attempted, 570 succeeded, 11 failed.",
    "<strong>July 30, 10:37 a.m. — records request filed</strong> with an "
    "immediate preservation notice to the City’s records access officer, "
    "copied to the Superintendent, the district’s counsel and others.",
    "<strong>July 30 — written notice.</strong> Separate security notices went "
    "to the Superintendent and School Committee members at about 1:51, 2:05, "
    "2:09 and 2:20 p.m. Eastern, and a Rule 31 public petition was filed at "
    "6:59 p.m.",
    "<strong>August 13, 2026 — School Committee.</strong> The petition appeared "
    "on the official agenda as c&p 6-13, recommending “Refer to "
    "Administration.” No approved-minute record of the final motion or vote "
    "has been located.",
    "<strong>August 25, 2026 — appeal.</strong> With no written response, "
    "exemption claim, fee estimate or production located, an appeal was filed "
    "with the Massachusetts Supervisor of Records. A separate Netlify-specific "
    "appeal was filed the same night and remains a distinct track.",
    "<strong>August 26, 2026 — Worcester explains the nonresponse.</strong> "
    "Records Access Officer Michael Manning wrote that the July 30 request had "
    "triggered the City’s own phishing rule and been diverted into a "
    "quarantined folder he could not access, and that he had not been notified "
    "of the diversion. He opened it as <strong>W094042-082626</strong>.",
    "<strong>September 1 and 3, 2026 — SPR26/3372.</strong> The Supervisor "
    "acknowledged the appeal, then ordered Worcester to respond within ten "
    "business days, expressly preserving the right to appeal the substantive "
    "response.",
    "<strong>September 10, 2026 — first substantive response.</strong> "
    "Searching the request’s terms individually returned approximately "
    "<strong>184,407</strong> responsive communications. Worcester proposed "
    "combined-term searches and no more than six of them; the requester agreed "
    "to narrow. Worcester reported no responsive records for Item 4F "
    "(notification, public warning, regulatory reporting).",
    "<strong>September 11, 2026 — partial production.</strong> Items 4A and 4B "
    "produced call-detail material, technical records and search screenshots, "
    "redacted under Exemptions (a), (b) and (c). A Google Vault screen for "
    "Jean Pray reported <strong>Count 0</strong> under a nine-term query.",
    "<strong>September 18, 2026 — the search is questioned.</strong> The "
    "narrowed 4D search produced 550 “hits” and a waived fee. The same day, "
    "the requester asked whether the Vault terms had been run conjunctively, "
    "whether the zero-result finding rested on that query alone, and whether "
    "broader searches had been run.",
    "<strong>September 29, 2026 — second search, 118 pages.</strong> Worcester "
    "stated that the September 18 inquiry led to a second search "
    "“which returned a result of 118 pages of email correspondences,” and "
    "produced them.",
    "<strong>October 12, 2026 — next production.</strong> Approximately "
    "<strong>594 pages</strong> were reported as under review, with about "
    "one-fifth reviewed as of September 30.",
]

ESTABLISHED = [
    "The campaign was real, and the preserved recipient copy was not ordinary "
    "display-name spoofing: Gmail recorded SPF, DKIM and DMARC passes and the "
    "recomputed signed body hash matched the body containing the Netlify link.",
    "Worcester’s technical response was fast — an investigation opened within "
    "minutes of the earliest produced campaign row, and a bulk deletion "
    "completed by 8:43:37 a.m.",
    "That first recorded deletion pass was not reported as 100 percent "
    "successful: 581 attempts, 570 successes, 11 failures.",
    "Jean Pray was in fact communicating about the incident. The second search "
    "produced her alerting Paul Johnson about the secure email and describing "
    "broad BCC distribution.",
    "Worcester’s own IT treated Dr. Murray’s account credential as compromised. "
    "Paul Johnson reset her password and emailed “Bob Walt” in direct response "
    "to the incident alert. The record does not state the reason in Worcester’s "
    "own words, but an administrator does not reset an account credential in "
    "the middle of a phishing incident absent a reason to believe it was "
    "exposed. It is the closest thing in the produced record to an IT finding "
    "on the credential itself.",
    "The authenticated sending path could address arbitrary recipients. The "
    "message reached a parent who was never a district contact, and page 72 has "
    "Jean Pray reporting broad BCC distribution inside Worcester and to other "
    "districts. The record does not show where that recipient list came from.",
    "The initial Jean Pray zero-result search did not exhaust the responsive "
    "records. Worcester itself said the September 18 inquiry led to the second "
    "search.",
    "The public-records process materially changed the factual picture: the "
    "later evidence produced internal communications that directly addressed "
    "questions posed in the original July 30 request.",
]

NOT_ESTABLISHED = [
    "That 584 people received the message. 584 is a spreadsheet row count.",
    "That 581 unique people or mailboxes were targeted.",
    "That nobody clicked the link, or that anyone submitted credentials or "
    "other information.",
    "That the 11 failed deletion attempts remained visible in inboxes.",
    "That the nine later-timestamped spreadsheet rows were delivered after "
    "cleanup.",
    "That Dr. Murray personally sent the message, or that any particular "
    "access mechanism was used.",
    "That Dr. Murray’s Drive, contact list, Vault or other Workspace resources "
    "were read or exported.",
    "That Dr. Murray’s contacts were read. This is the claim most likely to be "
    "overstated. The records show that the sending path could address people the "
    "sender chose; they do not show that her address book was opened. A "
    "forwarding rule, a “send as” configuration, an API or relay, or a "
    "recipient list compiled entirely outside the account would each produce "
    "this same message without anyone reading her contacts. That the message "
    "reached a parent who was never a district contact shows the sending "
    "capability, not where the list came from.",
    "That Dr. Murray’s student records were accessed. Nothing in the produced "
    "material speaks to them in either direction.",
    "Why the original Jean Pray search was constructed with the particular "
    "string shown in the Vault screenshot.",
    "Any intentional withholding by Worcester or any particular employee.",
    "That the 118 pages are 118 pages of cybersecurity evidence. A page-by-page "
    "review puts the incident-specific material on pages 66, 68, 69, 71, 72, "
    "76, 87 and 104; the balance is ordinary administrative content.",
]

REASONABLY_ASSUMED = [
    "That Dr. Murray’s mailbox or an authenticated session belonging to it was "
    "compromised or misused. This is the most economical explanation of the "
    "established facts — the authenticated sending path, the IT credential "
    "reset, the broad BCC distribution on page 72, and a recipient who was "
    "never a district contact — and it cannot reasonably be ruled out.",
    "The password reset is consistent with two different situations: an attacker "
    "who knew the password, or an attacker holding a live session or delegated "
    "token that a password change alone does not fully displace. Both converge "
    "on account-level compromise. They differ on which artifact was taken.",
    "That the sender held district email addresses most economically follows "
    "from a compromised mailbox, though an externally compiled list remains "
    "possible and untested.",
    "This is an inference from the produced record, not a finding. Worcester has "
    "not stated it and no produced document draws it. It is precisely what the "
    "Gmail and Workspace audit records already requested would confirm or "
    "refute.",
]

OPEN_QUESTIONS = [
    "What was the final technical determination about the sending mechanism?",
    "Did Worcester conclude that a mailbox, session, OAuth token, delegation, "
    "API access or relay had been compromised or misused?",
    "How many unique recipients or mailboxes received the message, and can they "
    "be categorised without disclosing personally identifiable information?",
    "What explains the difference between 584 campaign rows and 581 deletion "
    "attempts?",
    "What caused the 11 deletion failures, and were all 11 remediated?",
    "Were campaign-wide click or form-submission metrics available?",
    "What is the complete native thread behind page 69 and the other clipped "
    "records?",
    "What did Paul Johnson communicate to Bob Walt, and what followed?",
    "What systems, custodians and query logic supported the September 10 "
    "no-records statement for Item 4F?",
    "Was there a written incident report, root-cause analysis or after-action "
    "review?",
    "What was the final School Committee disposition of c&p 6-13 on "
    "August 13?",
    "Was any direct notice ultimately sent to known or potentially affected "
    "recipients, and if so when and through what channel?",
]

PAGE_CSS = """<style>
/* Worcester Cybersecurity Records Project — page-scoped styles.
   Tokens only, so the Paper and Split variations keep working. */
.wcr-hero{padding-top:2.5rem}
.wcr-updated{margin:.25rem 0 0;color:var(--pdf-mid,#a0a0a0);font-size:.8125rem}
.wcr-panel{border:1px solid var(--pdf-line,#2a2a2a);background:var(--pdf-ink-1,#161616);padding:1.5rem 1.25rem;margin:1.5rem 0 0}
.wcr-panel--yes{border-left:3px solid var(--pdf-signal,#ff5a1f)}
.wcr-panel--no{border-left:3px solid var(--pdf-mid,#a0a0a0)}
.wcr-panel--assume{border-left:3px solid var(--pdf-signal-hi,#ffa366)}
.wcr-panel h2{margin-top:0}
.wcr-panel ul{margin-bottom:0}
.wcr-gallery{border:1px solid var(--pdf-line,#2a2a2a);background:var(--pdf-ink-1,#161616);padding:1.25rem;margin:1.5rem 0 0}
.wcr-gallery-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.25rem;margin:0}
.wcr-gallery-grid figure{margin:0}
.wcr-gallery-grid img{width:100%;height:auto;border:1px solid var(--pdf-line,#2a2a2a);border-radius:4px;background:#fff}
.wcr-gallery-grid figcaption{font-size:.8125rem;color:var(--pdf-mid,#a0a0a0);margin-top:.4rem;line-height:1.45}
.wcr-timeline{border:1px solid var(--pdf-line,#2a2a2a);background:var(--pdf-ink-1,#161616);padding:1.5rem 1.25rem;margin:1.5rem 0 0}
.wcr-timeline li{margin-bottom:.85rem}
.wcr-timeline li:last-child{margin-bottom:0}
.wcr-stat-range{font-size:1.125rem;letter-spacing:.01em;line-height:1.25;padding-top:.45rem}
.wcr-cta{border:1px solid var(--pdf-line,#2a2a2a);background:var(--pdf-ink-1,#161616);padding:1.5rem;margin:1.5rem 0 0}
@media (max-width:719px){.wcr-gallery-grid{grid-template-columns:1fr}}
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
        cls = ' class="pdf-stat-num wcr-stat-range"' if len(num) > 8 else \
              ' class="pdf-stat-num"'
        stat_cells.append(
            f'<div class="pdf-stat"><div{cls}>{esc(num)}</div>'
            f'<div class="pdf-stat-lbl">{esc(lbl)}</div></div>')
    stats = ('<div class="pdf-stats"><div class="pdf-stats-grid">'
             + "".join(stat_cells) + "</div></div>")

    hero_inner = "\n".join([
        p("Public records project", class_name="pdf-kicker"),
        h(1, esc(TITLE)),
        p("Reconstructing the July 30, 2026 phishing incident and Worcester "
          "Public Schools’ handling of it — from the records the district "
          "itself produced."),
        p("On the morning of July 30, 2026, a phishing message reached a "
          "Worcester family. The records request filed about it was then caught "
          "by the City’s own phishing filter. An appeal, a 184,407-result "
          "search, a zero-result Vault screen for a key employee, and a second "
          "search that produced 118 pages followed. This project assembles "
          "that record from the produced documents themselves."),
        buttons([
            ("Send us what you have", MAILTO_CONTACT, False),
            ("Read the full article", ARTICLE_URL, True),
            ("All projects", PROJECTS_URL, True),
        ]),
        html_block(stats),
        p(f"Last updated: {UPDATED}", class_name="wcr-updated"),
    ])
    blocks.append(group(hero_inner, attrs='{"align":"wide","className":"wcr-hero"}',
                        class_name="wcr-hero"))

    # 2. What the records establish / do not establish
    yes = group(h(2, "What the records establish") + "\n" + ul(ESTABLISHED),
                attrs='{"className":"wcr-panel wcr-panel--yes"}',
                class_name="wcr-panel wcr-panel--yes")
    no = group(h(2, "What the records do not establish") + "\n" + ul(NOT_ESTABLISHED),
               attrs='{"className":"wcr-panel wcr-panel--no"}',
               class_name="wcr-panel wcr-panel--no")
    assume = group(h(2, "What can reasonably be assumed pending further records")
                   + "\n"
                   + p("Neither established nor refuted. These are the "
                       "conclusions the produced record supports as the most "
                       "economical explanation, and that no source has stated. "
                       "They are what the audit records already requested would "
                       "confirm or refute.")
                   + "\n"
                   + ul(REASONABLY_ASSUMED),
                   attrs='{"className":"wcr-panel wcr-panel--assume"}',
                   class_name="wcr-panel wcr-panel--assume")
    blocks.append(yes)
    blocks.append(no)
    blocks.append(assume)

    # 3. Timeline
    blocks.append(group(h(2, "Timeline") + "\n" + ol(TIMELINE),
                        attrs='{"className":"wcr-timeline"}',
                        class_name="wcr-timeline"))

    # 4. Key records gallery
    figures = []
    order = ["66", "68", "69", "71", "72", "76", "87", "104", "agenda"]
    for key in order:
        cap, _fn = EXHIBITS[key]
        figures.append(
            f'<figure><img src="{attr(media[key])}" alt="{attr(cap)}" '
            f'loading="lazy"><figcaption>{esc(cap)}</figcaption></figure>')
    gallery = ('<div class="wcr-gallery"><div class="wcr-gallery-grid">'
               + "".join(figures) + "</div></div>")
    gallery_block = group(h(2, "Key records from the 118-page production")
                          + "\n"
                          + p("Eight incident-specific pages, plus the official "
                              "August 13 agenda item. The remaining 110 pages of "
                              "the production are routine administrative "
                              "material. The full production is a redacted "
                              "public-records document containing third-party "
                              "material, so only these crops are published.")
                          + "\n"
                          + html_block(gallery),
                          attrs='{"className":"wcr-gallery-wrap"}',
                          class_name="wcr-gallery")
    blocks.append(gallery_block)

    # 5. Open questions
    blocks.append(group(h(2, "Open questions for the next production") + "\n"
                        + ul(OPEN_QUESTIONS),
                        attrs='{"className":"wcr-panel"}',
                        class_name="wcr-panel"))

    # 6. Footer CTA
    cta = group(h(2, "Add to this record") + "\n"
                + p("If you hold a responsive record from this incident — a "
                    "call log, a ticket, an internal email, or a copy of "
                    "something Worcester produced — send it to us. Corrections "
                    "to anything published here are welcome.")
                + "\n"
                + buttons([
                    (f"Email {CONTACT}", MAILTO_CONTACT, False),
                    ("Read the full article", ARTICLE_URL, True),
                    ("Donate", DONATE_URL, True),
                ]),
                attrs='{"className":"wcr-cta"}',
                class_name="wcr-cta")
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