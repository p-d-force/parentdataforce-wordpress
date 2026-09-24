#!/usr/bin/env python3
"""Build and idempotently publish the Massachusetts Student Settlement Records
Project page on parentdataforce.com/news.

Reads a sanitized districts snapshot JSON (from the project handoff packet,
regenerated from the tracker sheet for each refresh) and creates or updates the
WordPress page via REST. Content is fully static HTML blocks; a small vanilla
script block adds progressive enhancement (search, status filter chips, copy
button). The page must remain usable with JavaScript disabled.

Usage (run from tools/):

    python build_settlements_page.py --snapshot "G:/path/districts_snapshot.json" [--status draft|publish]

Stdlib only. Credentials come from ../rest/credentials.json via wp_api.
"""
import argparse
import html
import json
import os
import sys

import wp_api

SLUG = "massachusetts-student-settlement-records-project"
TITLE = "Massachusetts Student Settlement Records Project"
PAGE_TEMPLATE = "page-no-title"
CONTACT = "joey@parentdataforce.com"
MAILTO_REQUEST = (
    "mailto:joey@parentdataforce.com"
    "?subject=Please%20add%20my%20district%20to%20the%20Student%20Settlement%20Records%20Project"
    "&body=District%20name%3A%0ATown%2FCity%3A%0A"
)

# Only these tracker fields may ever reach the public page (see
# 06_DATA_MODEL_AND_SYNC_RULES.md). Everything else is internal.
WHITELIST = (
    "district",
    "jurisdiction",
    "submitted",
    "expected_initial_response",
    "status",
    "status_label",
    "public_note",
    "records_url",
    "last_public_update",
)

STATUS_BADGES = {
    "awaiting_initial_response": "Awaiting",
    "acknowledged": "Acknowledged",
    "routing_portal": "Routing / portal",
    "response_fee_estimate": "Response / fee estimate",
    "appeal_filed": "Appeal filed",
    "records_received_review_pending": "Records received",
    "partial_production": "Partial",
    "complete_published": "Complete",
    "no_responsive_records": "No records",
    "appeal_compliance": "Appeal / compliance",
}

DOC_KIND_LABELS = {"request": "Request", "response": "Response", "appeal": "Appeal"}

# Verbatim copy/paste template from
# 03_PUBLIC_RECORDS_REQUEST_TEMPLATE.md (the fenced ```text block).
REQUEST_TEMPLATE = r"""Hi,


Here is the reusable template for the Massachusetts school-district public records request. Replace the bracketed placeholders before sending.


Subject: [DISTRICT NAME] — Massachusetts Public Records Request — Student Settlement Agreements, MOUs, MOAs & Resolution Agreements (Sept. 18, 2021–Present)


Dear [RAO NAME / Records Access Officer]:


Pursuant to the Massachusetts Public Records Law, G.L. c. 66, § 10, and 950 C.M.R. 32.00, I request electronic copies of the following records maintained by [DISTRICT NAME].


TIME PERIOD


This request covers records entered into, executed, finalized, materially amended, or extended from September 18, 2021 through the date of your response.


RECORDS REQUESTED


Please provide all final or executed student-related agreements resolving, compromising, settling, memorializing, or otherwise disposing of a dispute, claim, complaint, appeal, due-process matter, grievance, or other contested educational issue involving [DISTRICT NAME], including:


- Settlement agreements and settlement-and-release agreements;


- Resolution agreements;


- Memoranda of Understanding (MOUs);


- Memoranda of Agreement (MOAs);


- Mediation agreements;


- Stipulations, consent agreements, or agreements for judgment/resolution;


- Side agreements, side letters, or similar written agreements;


- Amendments, addenda, extensions, or attachments that materially alter or form part of such agreements; and


- Any other final written agreement, regardless of title, that resolves or memorializes the resolution of a student-related educational dispute.


This includes agreements involving SPECIAL EDUCATION matters, including but not limited to IDEA/G.L. c. 71B, BSEA matters, Section 504, ADA-related educational access, evaluations, eligibility, placement, services, accommodations, compensatory education, tuition or reimbursement, transportation, extended-school-year services, or other special-education rights or services.


It also includes agreements involving GENERAL EDUCATION students or student matters, including, where applicable, student discipline or exclusion, access to educational programming, bullying/harassment or discrimination complaints, civil-rights complaints, educational services, enrollment, or other student-related disputes resolved through a written agreement.


This request is limited to STUDENT/EDUCATION matters.


EXPRESS EXCLUSION — NO STAFF OR EMPLOYMENT RECORDS


I am not requesting any agreement whose subject is a District employee, former employee, applicant, administrator, teacher, staff member, bargaining unit, or employment relationship. Please exclude collective-bargaining agreements, employee grievances, personnel settlements, employment discrimination matters, separation agreements, staff discipline matters, workers' compensation matters, and other employee/labor agreements.


I am likewise not seeking ordinary vendor, procurement, construction, property, or commercial settlements unrelated to student educational matters.


EXISTING LISTS OR INDEXES


If the District already maintains an existing log, index, spreadsheet, database export, or other existing record identifying responsive student-related agreements during this period, please include that existing record as well, with student PII redacted as necessary. I am not asking the District to create a new index or summary.


NO STUDENT PII REQUESTED


I am expressly NOT requesting personally identifiable student information.


The District may redact student names, parent/guardian names where identifying, addresses, contact information, student identification numbers, dates of birth, and any other direct or indirect identifier that must be removed under FERPA, Massachusetts student-record law, or another applicable law.


For special-education settlement agreements in particular, Champa v. Weston Public Schools, 473 Mass. 86 (2015), establishes that the presence of protected student information does not permit categorical withholding of the entire agreement. Personally identifiable information may be redacted, but segregable non-exempt portions are subject to disclosure.


The Supervisor of Records subsequently applied Champa in SPR17/661, Alexander v. Wellesley Public Schools (May 25, 2017), rejecting the argument that Champa was limited only to out-of-district settlement agreements and finding that the school had not met its burden to establish that in-district special-education settlement agreements could be withheld in their entirety.


DESE has also reiterated publicly that, in Massachusetts, settlement agreements between school districts and parents of students eligible for special education are public records once all personally identifiable information has been removed.


Accordingly, please do not withhold an entire responsive agreement merely because it contains some protected information, a confidentiality provision, or student-record material. Please redact only the information that is lawfully exempt and produce all reasonably segregable non-exempt portions.


If the District contends that any responsive agreement must be withheld in its entirety, please identify the record or category of records, the specific statutory exemption or privilege relied upon, and the factual basis explaining why redaction or segregation cannot permit disclosure of any portion, as required by G.L. c. 66, § 10(b)(iv).


ELECTRONIC PRODUCTION


Please provide all records electronically.


For agreements maintained as electronic documents or PDFs, please provide searchable electronic copies where available rather than printing and rescanning them. Native electronic format is welcome where practical. Please transmit records by email, shared download link, or another electronic delivery method.


No paper copies are requested, and I do not authorize costs associated solely with printing electronically maintained records.


ROLLING PRODUCTION


If responsive records can be produced in batches, please provide them on a rolling basis rather than delaying production of readily available records until the entire request has been completed.


FEES / PUBLIC INTEREST


This request is noncommercial and is intended to contribute to public understanding of the District's use of public funds and its resolution of student-related educational disputes. I therefore request waiver or reduction of any permissible fees under G.L. c. 66, § 10(d)(v).


If the District anticipates any fee, please provide the written, itemized, good-faith estimate required by G.L. c. 66, § 10(b)(viii), identifying the actual tasks, time, rate, and factual basis for each component. If a reasonable modification would materially reduce cost or burden while preserving the substance of the request, please identify that specific modification pursuant to G.L. c. 66, § 10(b)(vii).


If no responsive records exist for a particular category, please simply state that.


Please confirm receipt of this request.


Thank you,


[YOUR NAME]
[ORGANIZATION, IF ANY]"""

MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)
MONTHS_SHORT = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

HERO_KICKER = "Public records project"
HERO_SUBHEAD = (
    "Tracking how public school districts resolve student-related educational "
    "disputes — district by district."
)
HERO_INTRO = (
    "Parent Data Force is sending the same focused public-records request across "
    "Massachusetts to better understand how school districts resolve student-related "
    "educational disputes. We are asking for final written settlement and resolution "
    "agreements from September 18, 2021 to the present, with student-identifying "
    "information redacted as required by law."
)

REQUEST_INTRO = (
    "Each district receives a request for final or executed written agreements that "
    "resolve or memorialize student-related educational disputes, regardless of title:"
)
REQUEST_ITEMS = (
    "Settlement agreements and settlement-and-release agreements",
    "Resolution agreements",
    "Memoranda of Understanding (MOUs) and Memoranda of Agreement (MOAs)",
    "Mediation agreements",
    "Stipulations, consent agreements, or agreements for judgment/resolution",
    "Side agreements and side letters",
    "Amendments, addenda, extensions, or material attachments to such agreements",
    "Any other final written agreement resolving a student-related educational dispute",
)
PRIVACY_LEAD = "We are not requesting personally identifiable student information."
PRIVACY_BODY = (
    "The request expressly allows districts to redact student names, parent/guardian "
    "names where identifying, addresses, student numbers, dates of birth, and other "
    "personally identifiable information protected by law."
)

CTA_HEAD = "Don’t see your district? Ask us to add it."
CTA_SUPPORT = "Just send the district name and town/city. No student information is needed."

TEMPLATE_INTRO = (
    "Want to send the request yourself? Use our complete copy-and-paste template. "
    "You can adapt the district name, Records Access Officer, and signature and "
    "submit it directly to your school district."
)
TEMPLATE_INSTRUCTIONS = (
    "Replace the bracketed district and RAO placeholders.",
    "Verify the district’s current Records Access Officer or official submission address.",
    "Replace the signature with your own name/organization.",
    "Keep a copy of the sent request and acknowledgment.",
    "Do not add student personally identifiable information merely to use this template.",
)

RECORDS_EMPTY_HEAD = "Responses are beginning to arrive."
RECORDS_EMPTY_BODY = (
    "Parent Data Force has received acknowledgments, routing confirmations, and "
    "the first substantive fee-estimate response. No responsive settlement-record "
    "production has been published yet. As records arrive, they will be reviewed "
    "for privacy, indexed, summarized, and posted when appropriate. Appeals and "
    "compliance disputes will also be tracked here."
)

LEGAL_PARA_1 = (
    "The request invokes the Massachusetts Public Records Law, G.L. c. 66, § 10, and "
    "its implementing regulation, 950 C.M.R. 32.00. For special-education settlement "
    "agreements, the Massachusetts Supreme Judicial Court’s decision in "
    "<em>Champa v. Weston Public Schools</em>, 473 Mass. 86 (2015), requires "
    "disclosure of properly redacted settlement agreements once personally identifying "
    "information is removed. The Supervisor of Records applied <em>Champa</em> in "
    "SPR17/661, <em>Alexander v. Wellesley Public Schools</em> (2017), and the "
    "Department of Elementary and Secondary Education has stated publicly that "
    "special-education settlement agreements are public records once stripped of all "
    "personally identifiable information."
)
LEGAL_PARA_2 = (
    "The existence of a settlement does not prove wrongdoing, and a missed expected "
    "date on this tracker does not by itself mean a district violated the law. A "
    "response can be an acknowledgment, a fee estimate, a lawful extension, a "
    "production schedule, or a complete production. This page reports what was "
    "requested, what each district said, and what the produced records show."
)
LEGAL_LINKS = (
    ("Massachusetts law about special education", "https://www.mass.gov/info-details/massachusetts-law-about-special-education"),
    ("Selected Massachusetts and federal court cases", "https://www.mass.gov/info-details/select-massachusetts-and-federal-court-cases-for-law-about-pages-e-f"),
    ("DESE — Other Matters (2025)", "https://www.mass.gov/info-details/department-of-elementary-and-secondary-education-other-matters-1"),
    ("Audit of the Department of Elementary and Secondary Education (Aug. 26, 2025)", "https://www.mass.gov/audit/audit-of-the-department-of-elementary-and-secondary-education-august-26-2025"),
)

FAQ = (
    ("What exactly are you asking districts for?",
     "Final or executed written agreements that resolve student-related educational "
     "disputes, including settlements, resolution agreements, MOUs/MOAs, mediation "
     "agreements, stipulations, side agreements, and material amendments or addenda."),
    ("Are you asking for student names?",
     "No. The request expressly says Parent Data Force is not requesting personally "
     "identifiable student information."),
    ("Why track this statewide?",
     "Comparing districts can show how student disputes are being resolved, what "
     "remedies appear, how transparent districts are, and whether recurring patterns "
     "emerge. Any conclusions should be based on the records actually produced."),
    ("Can I request my district?",
     "Yes. Email <a href=\"mailto:{contact}\">{contact}</a> with the district name and "
     "municipality. No student information is needed."),
    ("Can I use the request myself?",
     "Yes. The full template is provided on the page so families, journalists, "
     "researchers, and community members can adapt it."),
    ("What does “expected response” mean?",
     "It is the current response milestone tracked for the request. It does not "
     "necessarily mean all records will be produced by that date; a response may "
     "include an acknowledgment, fee estimate, extension, production schedule, or "
     "other legally permitted response."),
    ("Will you publish everything you receive?",
     "Records should be reviewed first. The project should not publish "
     "student-identifying information or material that should remain private."),
    ("What happens if a district does not respond?",
     "The project follows up with the district. If no adequate response follows, the "
     "next step is an appeal to the Supervisor of Public Records under G.L. c. 66, "
     "§ 10A — the route this project has used elsewhere."),
    ("How can I report a correction?",
     "Email <a href=\"mailto:{contact}\">{contact}</a> and identify the district and "
     "the information you believe needs to be corrected."),
)

FOOTER_CTA = (
    "Help expand the project. Request a district, share the page, and check back "
    "as records are published."
)

ENHANCEMENT_CSS = """<style>
/* Student Settlement Records — page-scoped styles. Tokens from pdf-design.css. */
.pssr-hero{padding-top:2.5rem}
.pssr-stat-range{font-size:1.125rem;letter-spacing:.01em;line-height:1.25;padding-top:.45rem}
.pssr-updated{margin:.25rem 0 0;color:var(--pdf-mid,#a0a0a0);font-size:.8125rem}
.pssr-controls{display:flex;flex-wrap:wrap;gap:.75rem;align-items:center;margin:0 0 .75rem}
.pssr-search{flex:1 1 15rem;min-width:0;max-width:26rem;background:var(--pdf-ink-1,#161616);border:1px solid var(--pdf-line,#2a2a2a);color:var(--pdf-paper,#f5f5f5);font-family:var(--pdf-mono,monospace);font-size:.875rem;padding:.625rem .875rem;border-radius:999px}
.pssr-search:focus{outline:2px solid var(--pdf-signal,#ff5a1f);outline-offset:1px}
.pssr-tabs{margin:0;padding:0;max-width:none}
.pssr-count{margin:0 0 .9rem;font-family:var(--pdf-mono,monospace);font-size:.75rem;letter-spacing:.06em;text-transform:uppercase;color:var(--pdf-mid,#a0a0a0)}
.pssr-table{overflow-x:auto}
.pssr-table table{border-collapse:collapse;font-size:.9375rem;line-height:1.4;margin:0}
.pssr-table table,.pssr-table thead,.pssr-table tbody,.pssr-table tr,.pssr-table td,.pssr-table th{border:0}
.pssr-table thead th{padding:.75rem;font-family:var(--pdf-mono,monospace);font-size:.6875rem;font-weight:500;letter-spacing:.12em;text-transform:uppercase;color:var(--pdf-mid,#a0a0a0);text-align:left;vertical-align:bottom;border-bottom:1px solid var(--pdf-mid,#a0a0a0);white-space:nowrap}
.pssr-table tbody td{padding:.7rem .75rem;border-bottom:1px solid var(--pdf-line,#2a2a2a);vertical-align:top}
.pssr-table tbody tr:nth-child(even) td{background:rgba(245,245,245,.03)}
.pssr-table tbody tr:hover td{background:var(--pdf-ink-1,#161616)}
.pssr-district{font-weight:600;min-width:12rem}
.pssr-timeline{font-family:var(--pdf-mono,monospace);font-size:.8125rem;color:var(--pdf-mid,#a0a0a0);white-space:nowrap;font-variant-numeric:tabular-nums}
.pssr-timeline .pssr-expected{color:var(--pdf-paper,#f5f5f5)}
.pssr-expected.is-overdue{color:var(--pdf-signal,#ff5a1f);font-weight:600}
.pssr-status{min-width:10rem}
.pssr-status .pssr-badge{margin:0 .35rem .35rem 0}
.pssr-note{font-size:.8125rem;color:rgba(245,245,245,.85);min-width:16rem;max-width:26rem}
.pssr-docs{font-family:var(--pdf-mono,monospace);font-size:.8125rem;white-space:nowrap}
.pssr-docs a{color:var(--pdf-signal-hi,#ffa366);text-decoration:none}
.pssr-docs a:hover{color:var(--pdf-signal,#ff5a1f);text-decoration:underline}
.pssr-docsep{color:var(--pdf-line,#2a2a2a);padding:0 .3rem}
@media (min-width:900px){
\t.pssr-table{overflow:visible}
\t.pssr-table thead th{position:sticky;top:0;z-index:2;background:var(--pdf-ink-0,#0b0b0b)}
}
@media (max-width:719px){
\t.pssr-controls{flex-direction:column;align-items:stretch}
\t.pssr-search{flex-basis:auto;max-width:none}
\t.pssr-table{overflow:visible}
\t.pssr-table table,.pssr-table tbody,.pssr-table tr,.pssr-table td{display:block;width:100%}
\t.pssr-table thead{display:none}
\t.pssr-table tbody tr{border:1px solid var(--pdf-line,#2a2a2a);border-radius:10px;background:var(--pdf-ink-1,#161616);padding:.4rem 1rem .55rem;margin:.75rem 0}
\t.pssr-table tbody tr:nth-child(even) td{background:transparent}
\t.pssr-table tbody tr:hover td{background:transparent}
\t.pssr-table tbody td{border:0;padding:.34rem 0;display:flex;justify-content:space-between;align-items:baseline;gap:1rem}
\t.pssr-table tbody td::before{content:attr(data-label);flex:0 0 auto;font-family:var(--pdf-mono,monospace);font-size:.625rem;letter-spacing:.12em;text-transform:uppercase;color:var(--pdf-mid,#a0a0a0);padding-top:.15em}
\t.pssr-table td.pssr-district{display:block;font-size:1rem;padding:.3rem 0 .45rem}
\t.pssr-table td.pssr-district::before{content:none}
\t.pssr-table td.pssr-note{display:block;padding-top:.4rem}
\t.pssr-table td.pssr-note::before{display:block;margin-bottom:.25rem}
}
.pssr-badge{display:inline-block;font-family:var(--pdf-mono,monospace);font-size:.6875rem;letter-spacing:.08em;text-transform:uppercase;padding:.25rem .5rem;border:1px solid var(--pdf-mid,#a0a0a0);border-radius:999px;color:var(--pdf-mid,#a0a0a0);white-space:nowrap}
.pssr-badge--acknowledged{border-color:var(--pdf-signal-hi,#ffa366);color:var(--pdf-signal-hi,#ffa366)}
.pssr-badge--records_received_review_pending,.pssr-badge--partial_production{border-color:var(--pdf-signal,#ff5a1f);color:var(--pdf-signal,#ff5a1f)}
.pssr-badge--complete_published,.pssr-badge--appeal_compliance{background:var(--pdf-signal,#ff5a1f);border-color:var(--pdf-signal,#ff5a1f);color:#160801;font-weight:700}
.pssr-cta{border:1px solid var(--pdf-line,#2a2a2a);background:var(--pdf-ink-1,#161616);padding:1.5rem}
.pssr-template{border:1px solid var(--pdf-line,#2a2a2a);background:var(--pdf-ink-1,#161616)}
.pssr-template summary{cursor:pointer;padding:1rem 1.25rem;font-family:var(--pdf-mono,monospace);font-size:.8125rem;letter-spacing:.08em;text-transform:uppercase;color:var(--pdf-signal,#ff5a1f)}
.pssr-template[open] summary{border-bottom:1px solid var(--pdf-line,#2a2a2a)}
.pssr-template-tools{padding:1rem 1.25rem 0}
.pssr-copy{font-family:var(--pdf-mono,monospace);font-size:.75rem;letter-spacing:.12em;text-transform:uppercase;padding:.5rem 1rem;border:1px solid var(--pdf-line,#2a2a2a);border-radius:999px;color:var(--pdf-paper,#f5f5f5);background:transparent;cursor:pointer}
.pssr-copy:hover{border-color:var(--pdf-signal,#ff5a1f);color:var(--pdf-signal,#ff5a1f)}
.pssr-template pre{white-space:pre-wrap;word-break:break-word;margin:0;padding:1.25rem;max-height:32rem;overflow:auto;font-size:.8125rem;line-height:1.55;color:var(--pdf-paper,#f5f5f5)}
.pssr-appeal{border:1px solid var(--pdf-line,#2a2a2a);background:var(--pdf-ink-1,#161616);padding:1.25rem;margin-top:1rem}
.pssr-appeal-docs{font-size:.875rem}
.pssr-badge--routing_portal{border-color:var(--pdf-mid,#a0a0a0);color:var(--pdf-mid,#a0a0a0)}
.pssr-badge--response_fee_estimate{border-color:var(--pdf-signal-hi,#ffa366);color:var(--pdf-signal-hi,#ffa366)}
.pssr-badge--appeal_filed{background:var(--pdf-signal,#ff5a1f);border-color:var(--pdf-signal,#ff5a1f);color:#160801;font-weight:700}
.pssr-badge--fee-estimate{border-color:var(--pdf-mid,#a0a0a0);color:var(--pdf-mid,#a0a0a0)}
@media (max-width:719px){.pssr-badge{white-space:normal}}
</style>"""

ENHANCEMENT_JS = """<script>
(function () {
	"use strict";
	var doc = document;
	var table = doc.querySelector(".pssr-table table");
	var search = doc.querySelector(".pssr-search");
	var chips = Array.prototype.slice.call(doc.querySelectorAll(".pssr-chip"));
	var empty = doc.querySelector(".pssr-empty");
	var count = doc.querySelector(".pssr-count");
	var rows = table ? Array.prototype.slice.call(table.querySelectorAll("tbody tr")) : [];
	var today = new Date();
	today.setHours(0, 0, 0, 0);
	rows.forEach(function (tr) {
		if (tr.getAttribute("data-status") !== "awaiting_initial_response") { return; }
		var exp = tr.getAttribute("data-expected");
		if (!exp) { return; }
		if (today > new Date(exp + "T00:00:00")) {
			var span = tr.querySelector(".pssr-expected");
			if (span) {
				span.classList.add("is-overdue");
				tr.title = "Past the expected initial-response date";
			}
		}
	});
	var status = "all";
	function apply() {
		if (!rows.length) { return; }
		var q = search && search.value ? search.value.trim().toLowerCase() : "";
		var shown = 0;
		rows.forEach(function (tr) {
			var ok = (status === "all" || tr.getAttribute("data-status") === status) &&
				(!q || (tr.getAttribute("data-district") || "").indexOf(q) !== -1);
			tr.hidden = !ok;
			if (ok) { shown++; }
		});
		if (empty) { empty.hidden = shown > 0; }
		if (count) { count.hidden = false; count.textContent = "Showing " + shown + " of " + rows.length + " districts"; }
	}
	if (search) { search.addEventListener("input", apply); }
	// Initial pass: fill the visible count (rows already render server-side).
	apply();
	chips.forEach(function (chip) {
		chip.addEventListener("click", function () {
			status = chip.getAttribute("data-status") || "all";
			chips.forEach(function (c) { c.classList.toggle("is-active", c === chip); });
			apply();
		});
	});
	var wireCopy = function () {
		var copyBtn = doc.querySelector(".pssr-copy");
		if (!copyBtn) { return; }
		copyBtn.addEventListener("click", function () {
			var box = copyBtn.closest(".pssr-template") || doc;
			var pre = box.querySelector("pre");
			if (!pre || !navigator.clipboard) { return; }
			navigator.clipboard.writeText(pre.textContent).then(function () {
				var old = copyBtn.textContent;
				copyBtn.textContent = "Copied.";
				setTimeout(function () { copyBtn.textContent = old; }, 2000);
			}, function () {});
		});
	};
	// The template <details> renders after this script block in DOM order.
	if (doc.readyState === "loading") { doc.addEventListener("DOMContentLoaded", wireCopy); }
	else { wireCopy(); }
})();
</script>"""


def fmt_long(iso):
    """2026-09-21 -> September 21, 2026"""
    y, m, d = (int(p) for p in iso.split("-"))
    return f"{MONTHS[m - 1]} {d}, {y}"


def fmt_short(iso):
    """2026-10-02 -> Oct 2, 2026"""
    y, m, d = (int(p) for p in iso.split("-"))
    return f"{MONTHS_SHORT[m - 1]} {d}, {y}"


def esc(text):
    return html.escape(str(text), quote=False)


def attr(text):
    return html.escape(str(text), quote=True)


def sanitize(snapshot):
    """Keep only whitelisted fields; fail loudly on unknown status."""
    rows = snapshot.get("districts")
    if not isinstance(rows, list) or not rows:
        sys.exit("snapshot has no 'districts' list")
    clean = []
    for i, row in enumerate(rows):
        missing = [k for k in ("district", "jurisdiction", "submitted",
                               "expected_initial_response", "status") if not row.get(k)]
        if missing:
            sys.exit(f"row {i}: missing required field(s): {', '.join(missing)}")
        status = row["status"]
        if status not in STATUS_BADGES:
            sys.exit(f"row {i} ({row['district']}): unknown status {status!r} — refusing to guess")
        clean.append({k: row.get(k) for k in WHITELIST})
    return clean


# ---- block builders -------------------------------------------------------

def p(text, class_name=None):
    open_tag = f'<!-- wp:paragraph {{"className":"{class_name}"}} -->' if class_name else "<!-- wp:paragraph -->"
    cls = f' class="{attr(class_name)}"' if class_name else ""
    return f"{open_tag}\n<p{cls}>{text}</p>\n<!-- /wp:paragraph -->"


def h(level, text):
    return f'<!-- wp:heading {{"level":{level}}} -->\n<h{level} class="wp-block-heading">{text}</h{level}>\n<!-- /wp:heading -->'


def ul(items):
    lis = "\n".join(
        f"<!-- wp:list-item -->\n<li>{it}</li>\n<!-- /wp:list-item -->" for it in items
    )
    return f"<!-- wp:list -->\n<ul>{lis}</ul>\n<!-- /wp:list -->"


def ol(items):
    lis = "\n".join(
        f"<!-- wp:list-item -->\n<li>{it}</li>\n<!-- /wp:list-item -->" for it in items
    )
    return f'<!-- wp:list {{"ordered":true}} -->\n<ol>{lis}</ol>\n<!-- /wp:list -->'


def buttons(items):
    """items: list of (label, href, outline_bool)"""
    parts = []
    for label, href, outline in items:
        cls = ' {"className":"is-style-outline"}' if outline else ""
        div = 'wp-block-button is-style-outline' if outline else 'wp-block-button'
        parts.append(
            f"<!-- wp:button{cls} -->\n"
            f'<div class="{div}"><a class="wp-block-button__link wp-element-button" href="{attr(href)}">{label}</a></div>\n'
            f"<!-- /wp:button -->"
        )
    inner = "\n".join(parts)
    return f'<!-- wp:buttons -->\n<div class="wp-block-buttons">{inner}</div>\n<!-- /wp:buttons -->'


def group(inner, attrs="", anchor=None, class_name=None):
    open_comment = f"<!-- wp:group {attrs} -->" if attrs else "<!-- wp:group -->"
    div_cls = "wp-block-group" + (f" {class_name}" if class_name else "")
    div_id = f' id="{attr(anchor)}"' if anchor else ""
    return f"{open_comment}\n<div class=\"{div_cls}\"{div_id}>{inner}</div>\n<!-- /wp:group -->"


def html_block(raw):
    return f"<!-- wp:html -->\n{raw}\n<!-- /wp:html -->"


def qa_group(question, answer):
    inner = h(3, question) + "\n" + p(answer)
    attrs = ('{"style":{"border":{"top":{"color":"var:preset|color|accent-6","width":"1px"}},'
             '"spacing":{"padding":{"top":"var:preset|spacing|30","bottom":"var:preset|spacing|30"}}}}')
    return group(inner, attrs=attrs)


def build_blocks(project, rows, documents=()):
    total = len(rows)
    acknowledged = sum(1 for r in rows if r["status"] == "acknowledged")
    productions = sum(1 for r in rows if r.get("records_url"))
    appeals = sum(1 for r in rows if (r.get("appeal_note") or r["status"].startswith("appeal")))
    updated = fmt_long(project.get("snapshot_date") or rows[0]["last_public_update"])
    contact = CONTACT

    blocks = []

    # 1. Hero -------------------------------------------------------------
    stats = (
        '<div class="pdf-stats"><div class="pdf-stats-grid">'
        f'<div class="pdf-stat"><div class="pdf-stat-num">{total}</div>'
        f'<div class="pdf-stat-lbl">districts requested</div></div>'
        f'<div class="pdf-stat"><div class="pdf-stat-num">{acknowledged}</div>'
        f'<div class="pdf-stat-lbl">acknowledged</div></div>'
        f'<div class="pdf-stat"><div class="pdf-stat-num">{appeals}</div>'
        f'<div class="pdf-stat-lbl">SPR appeal filed</div></div>'
        f'<div class="pdf-stat"><div class="pdf-stat-num">{productions}</div>'
        f'<div class="pdf-stat-lbl">reviewed productions posted yet</div></div>'
        "</div></div>"
    )
    hero_inner = "\n".join([
        p(HERO_KICKER, class_name="pdf-kicker"),
        h(1, TITLE),
        p(HERO_SUBHEAD),
        p(HERO_INTRO),
        buttons([
            ("Request Your District", MAILTO_REQUEST, False),
            ("Use the Public Records Template", "#template", True),
        ]),
        html_block(stats),
        p(f"Last updated: {updated}", class_name="pssr-updated"),
    ])
    blocks.append(group(hero_inner, attrs='{"align":"wide","className":"pssr-hero"}', class_name="pssr-hero"))

    # 2. Overview ----------------------------------------------------------
    n = total
    overview = "\n".join([
        h(2, "Why this project exists"),
        p("Parent Data Force is sending substantially the same Massachusetts Public "
          "Records Law request to public school districts across the Commonwealth. "
          "The request seeks final or executed student-related agreements entered "
          "into, finalized, materially amended, or extended from September 18, 2021 "
          f"through the date of each district’s response. The project currently "
          f"covers {n} districts."),
        p("The request asks for final written agreements that resolve or memorialize "
          "student-related educational disputes — settlement agreements, resolution "
          "agreements, MOUs and MOAs, mediation agreements, stipulations and consent "
          "agreements, side agreements, material amendments and addenda, and other "
          "final written agreements. It covers both special-education and "
          "general-education disputes, including placement, services, evaluations, "
          "eligibility, accommodations, compensatory education, tuition and "
          "reimbursement, transportation, extended school year, discipline and "
          "exclusion, access to programming, bullying and harassment, "
          "discrimination, civil-rights complaints, and enrollment."),
        p("The request expressly excludes personally identifiable student "
          "information; staff and employment settlements; collective-bargaining and "
          "employee grievance matters; personnel discipline and separation matters; "
          "workers’ compensation; vendor, procurement, construction, and property "
          "disputes; and unrelated commercial matters. Districts may redact student "
          "names and other legally protected identifiers."),
        p("A statewide comparison can help show how student-related disputes are "
          "resolved, what remedies are used, how districts respond to public-records "
          "requests, and whether recurring patterns emerge. We do not claim a "
          "pattern until records actually support it, and we clearly distinguish "
          "what was requested, what a district said, and what the produced records "
          "show."),
    ])
    blocks.append(group(overview, attrs='{"anchor":"overview"}', anchor="overview"))

    # 3. What we are requesting ---------------------------------------------
    requesting = "\n".join([
        h(2, "What we are requesting"),
        p(REQUEST_INTRO),
        ul(REQUEST_ITEMS),
        p(f"<strong>{PRIVACY_LEAD}</strong> {PRIVACY_BODY}"),
    ])
    blocks.append(group(requesting))

    # 4. District tracker -----------------------------------------------------
    chips = ['<button type="button" class="pdf-tab pssr-chip is-active" data-status="all">All</button>']
    seen = [s for s in STATUS_BADGES if any(r["status"] == s for r in rows)]
    for s in seen:
        count = sum(1 for r in rows if r["status"] == s)
        chips.append(
            f'<button type="button" class="pdf-tab pssr-chip" data-status="{attr(s)}">'
            f'{STATUS_BADGES[s]} ({count})</button>'
        )
    controls = (
        '<div class="pssr-controls">'
        '<input type="search" class="pssr-search" placeholder="Search district or town…" '
        'aria-label="Search district or town">'
        f'<div class="pdf-tabs pssr-tabs">{"".join(chips)}</div>'
        "</div>"
    )

    head_cells = (
        "<tr>"
        '<th scope="col">District</th>'
        '<th scope="col">Timeline</th>'
        '<th scope="col">Status</th>'
        '<th scope="col">Latest public note</th>'
        '<th scope="col">Documents</th>'
        "</tr>"
    )
    docs_by_district = {}
    for d in documents:
        docs_by_district.setdefault(d["district"], []).append(d)
    body_rows = []
    for r in rows:
        note = esc(r["public_note"]) if r.get("public_note") else "—"
        data_district = attr(f"{r['district']} {r['jurisdiction']}".lower())
        badge = STATUS_BADGES[r["status"]]
        status_cell = f'<span class="pssr-badge pssr-badge--{attr(r["status"])}">{esc(badge)}</span>'
        if r.get("fee_estimate"):
            status_cell += (f' <span class="pssr-badge pssr-badge--fee-estimate">'
                            f'Fee estimate: {esc(r["fee_estimate"])}</span>')
        s_y, s_m, s_d = (int(x) for x in r["submitted"].split("-"))
        e_y, e_m, e_d = (int(x) for x in r["expected_initial_response"].split("-"))
        if s_y == e_y:
            timeline_head = f"{MONTHS_SHORT[s_m - 1]} {s_d} → "
            timeline_tail = f"{MONTHS_SHORT[e_m - 1]} {e_d}, {e_y}"
        else:
            timeline_head = fmt_short(r["submitted"]) + " → "
            timeline_tail = fmt_short(r["expected_initial_response"])
        docs = docs_by_district.get(r["district"])
        if docs:
            docs_cell = ' <span class="pssr-docsep">·</span> '.join(
                f'<a href="{attr(d["url"])}" title="{attr(d["label"])}">{DOC_KIND_LABELS[d["kind"]]}</a>'
                for d in docs)
        else:
            docs_cell = "—"
        body_rows.append(
            f'<tr data-district="{data_district}" data-status="{attr(r["status"])}" '
            f'data-submitted="{attr(r["submitted"])}" data-expected="{attr(r["expected_initial_response"])}">'
            f'<td class="pssr-district" data-label="District">{esc(r["district"])}</td>'
            f'<td class="pssr-timeline" data-label="Timeline">'
            f'<span>{timeline_head}</span><span class="pssr-expected">{timeline_tail}</span></td>'
            f'<td class="pssr-status" data-label="Status">{status_cell}</td>'
            f'<td class="pssr-note" data-label="Latest note">{note}</td>'
            f'<td class="pssr-docs" data-label="Documents">{docs_cell}</td>'
            "</tr>"
        )
    table_block = (
        '<!-- wp:table {"align":"wide","className":"pssr-table"} -->\n'
        '<figure class="wp-block-table alignwide pssr-table"><table>'
        f"<thead>{head_cells}</thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table></figure>\n"
        "<!-- /wp:table -->"
    )

    tracker_inner = "\n".join([
        h(2, "Live district tracker"),
        p(f"{total} districts have received the request. Use the search box or the "
          "status filters to narrow the table."),
        html_block(controls),
        html_block('<p class="pssr-count" hidden aria-live="polite"></p>'),
        table_block,
        html_block(ENHANCEMENT_CSS
                   + '\n<p class="pssr-empty" hidden>No districts match that filter.</p>\n'
                   + ENHANCEMENT_JS),
    ])
    blocks.append(group(tracker_inner, attrs='{"align":"wide","className":"pssr-tracker"}',
                        class_name="pssr-tracker alignwide", anchor="districts"))

    # 4b. Appeals & notable responses -----------------------------------------
    appeal_rows = [r for r in rows if r.get("appeal_note")]
    if appeal_rows:
        order = {"request": 0, "response": 1, "appeal": 2}
        docs_by_district = {}
        for d in documents:
            docs_by_district.setdefault(d["district"], []).append(d)
        for dl in docs_by_district.values():
            dl.sort(key=lambda d: order.get(d.get("kind"), 99))
        appeal_items = []
        for r in appeal_rows:
            inner = h(3, f"{esc(r['district'])} — fee estimate appealed") + "\n" + p(esc(r["appeal_note"]))
            docs = docs_by_district.get(r["district"])
            if docs:
                links = " · ".join(
                    f'<a href="{attr(d["url"])}">{esc(d["label"])}</a>' for d in docs)
                inner += "\n" + p(f"Source documents: {links}", class_name="pssr-appeal-docs")
            appeal_items.append(group(inner, class_name="pssr-appeal"))
        appeals_inner = h(2, "Appeals &amp; notable responses") + "\n" + "\n".join(appeal_items)
        blocks.append(group(appeals_inner))

    # 5. Request-your-district CTA -------------------------------------------
    cta_inner = "\n".join([
        h(2, CTA_HEAD),
        p(CTA_SUPPORT),
        buttons([("Request Your District", MAILTO_REQUEST, False)]),
    ])
    blocks.append(group(cta_inner, attrs='{"anchor":"request","className":"pssr-cta"}', anchor="request", class_name="pssr-cta"))

    # 6. Template section -------------------------------------------------------
    template_inner = "\n".join([
        h(2, "Use the request yourself"),
        p(TEMPLATE_INTRO),
        h(3, "How to use it"),
        ol(TEMPLATE_INSTRUCTIONS),
        html_block(
            '<details class="pssr-template">\n'
            "<summary>Open the full request template</summary>\n"
            '<div class="pssr-template-tools">'
            '<button type="button" class="pssr-copy">Copy template</button>'
            "</div>\n"
            f"<pre>{html.escape(REQUEST_TEMPLATE, quote=False)}</pre>\n"
            "</details>"
        ),
    ])
    blocks.append(group(template_inner, attrs='{"anchor":"template"}', anchor="template"))

    # 7. Records library -----------------------------------------------------
    records_inner = "\n".join([
        h(2, "Records library"),
        h(3, RECORDS_EMPTY_HEAD),
        p(RECORDS_EMPTY_BODY),
    ])
    blocks.append(group(records_inner, attrs='{"anchor":"records"}', anchor="records"))

    # 8. What happens when records arrive ---------------------------------------
    arrival = "\n".join([
        h(2, "What happens when records arrive"),
        p("When a district produces records, each production goes through the same "
          "process before it appears on this page:"),
        ol([
            "<strong>Received</strong> — the production is logged for the district.",
            "<strong>Privacy/relevance review</strong> — the production is checked "
            "against the request scope and for student personally identifiable "
            "information.",
            "<strong>Indexed and summarized</strong> — agreements are organized by "
            "district and summarized factually.",
            "<strong>Published with source documents</strong> — reviewed records "
            "are posted here with their sources.",
        ]),
        p("Records are reviewed before public posting to ensure student personally "
          "identifiable information is not inadvertently exposed — names, "
          "addresses, student IDs, dates of birth, and unique details that could "
          "re-identify a child. District redactions are not assumed to be "
          "sufficient on their own."),
    ])
    blocks.append(group(arrival))

    # 9. Legal context ---------------------------------------------------------
    legal = "\n".join([
        h(2, "Legal context"),
        p(LEGAL_PARA_1),
        p(LEGAL_PARA_2),
        ul([f'<a href="{attr(url)}">{esc(label)}</a>' for label, url in LEGAL_LINKS]),
    ])
    blocks.append(group(legal))

    # 10. FAQ ---------------------------------------------------------------------
    faq_inner = "\n".join([h(2, "Frequently asked questions")] + [
        qa_group(q.format(contact=contact), a.format(contact=contact)) for q, a in FAQ
    ])
    blocks.append(group(faq_inner, attrs='{"anchor":"faq"}', anchor="faq"))

    # 11. Footer CTA -----------------------------------------------------------------
    footer_inner = "\n".join([
        h(2, FOOTER_CTA),
        p(f'Email <a href="mailto:{contact}">{contact}</a> to request a district or '
          "report a correction."),
    ])
    blocks.append(group(footer_inner))

    return "\n\n".join(blocks) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--snapshot", required=True, help="path to districts_snapshot.json")
    ap.add_argument("--status", choices=("draft", "publish"), default="publish")
    args = ap.parse_args()

    with open(args.snapshot, encoding="utf-8-sig") as f:
        snapshot = json.load(f)
    rows = sanitize(snapshot)
    content = build_blocks(snapshot.get("project", {}), rows)

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
        "rows": len(rows),
        "content_chars": len(content),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
