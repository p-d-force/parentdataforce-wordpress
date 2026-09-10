# Parent Data Force — Project Handoff

> For ingestion into Mnemopi / a fresh Oh My Pi session. Read this first.
> Last updated: 2026-09-10 (design + deploy session).

---

## What this is

The WordPress news/records site for **Parent Data Force**, a Massachusetts
special-education and public-accountability advocacy org. Live at
**https://www.parentdataforce.com/news/**. The wider org site (static) lives at
parentdataforce.com; this repo is the WordPress `/news/` subsection.

- **Repo:** `C:/Users/paren/Development/parentdataforce-wordpress`
- **GitHub:** `https://github.com/p-d-force/parentdataforce-wordpress` (**PUBLIC**)
- **Local branch state:** history was rewritten (see SECURITY below) — `git push
  --force-with-lease origin main` is pending on the user.

## ⚠️ SECURITY — action still required

A plaintext password leaked into the public repo via
`docs/migration/parentdataforce_roadmap.md` (committed in `3ac8897`, pushed).
Contained the **live FTP/cPanel password** for `webmaster@parentdataforce.com`
and a WP login candidate. Already done locally: redacted the file and rewrote
history with `git filter-repo` (secrets scrubbed from all commits; backup mirror
at `_archive/pdforce-wprerewrite-backup.git`). **Still required from the user:**

1. **Rotate the FTP/cPanel password** (it still authenticated at discovery time).
   Then update `rest/credentials.json` → `ftp.password` locally (gitignored).
2. **Force-push** the rewritten history to GitHub.
3. Optionally make the repo private, and/or ask GitHub Support to purge cached
   commit views of the old SHAs.

Credentials never live in the repo. Real secrets are in
`rest/credentials.json` (**gitignored**): REST application password, FTP, and a
stale `login_password`.

## Access / how things connect

- **WP login username is `pdforce`** (user id 1, display name now **"Parent Data
  Force"**). `admin` is only a display name, NOT a registered login — this trap
  is why cookie `login_password` auth fails. Use the **application password**
  (`rest/credentials.json`) for REST.
- **REST client:** `rest/wp.py` (CLI) — posts, pages, categories, tags, users.
- **Deploy:** theme goes over **FTP**, not REST. `tools/deploy_theme.py` syncs
  `theme/pdforce/` → `/public_html/news/wp-content/themes/pdforce/`
  (incremental by remote size; `--all` forces full, `--dry-run` lists).

## The brand

Dark near-black `#0b0b0b`, greys (`#161616/#1d1d1d/#2a2a2a/#a0a0a0`), paper
`#f5f5f5`, and **one signal orange `#ff5a1f`** (+ hi `#ffa366`). JetBrains Mono
for labels/meta/ASCII. The logo is a **fault line / crack splitting a black disc
edge-to-edge** (NOT a lightning bolt). **The crack shape must stay exactly as
drawn and reach the disc edges** — the user is emphatic about this.

## Design system (built this session, deployed)

Reproducible pipeline:
- `tools/extract_logo.py` — traces the exact crack mask from
  `captures/live_logo.png` → `theme/pdforce/assets/images/bolt.svg`,
  `assets/js/bolt-ascii.js` (ASCII raster), `assets/js/bolt-path.js` (SVG path
  for the hero). Tips extended edge-to-edge along the fault axis, tapering.
  Env knobs: `BOLT_TOL`, `BOLT_COLS`.
- `tools/build_animated_logo.py` — `assets/images/logo-animated.svg`: spherical
  disc (offset light, limb darkening, specular), cracked-stone texture
  (procedural hairlines + grain), warm glow, shine sweep down the crack,
  drifting embers. Pure CSS animation, `prefers-reduced-motion` safe.
- `tools/design_checkpoint.py <label> ["note"]` — snapshots design assets into
  `designs/NNN-label/` (manifest + assets). 6 checkpoints saved.

Theme pieces (`theme/pdforce/`):
- `assets/js/pdforce-ascii.js` — the animated ASCII hero engine (Oh-My-Pi-TUI
  style, ported to canvas). The **logo is the centerpiece**; public-record
  glyphs (`▤`) drip out of the crack's lower tip and fall into a quiet rippling
  data field; sparse ember/starfield. Reduced-motion + IntersectionObserver +
  saveData safe. Emits records from the logo via `data-emit-from`.
- `assets/css/pdf-design.css` — hero, records docket, stats strip, article
  reading view, 404 scene.
- `patterns/hero-fault.php` (logo-centric hero), `patterns/docket.php` (records
  index query loop), `patterns/record-stats.php` (scraper stats strip),
  `patterns/hidden-404.php` (ASCII "signal lost" scene).
- Templates: `home.html` (hero+stats+docket), `archive.html` (docket),
  `single-long-form.html` (reading view), `404.html` (fault scene).
- `functions.php` — `pdforce_enqueue_design_assets()` loads the CSS + JS on
  home/archive/404/search.

## Content model

- **Scope categories:** `District Reports` (id 10, district-level) and
  `Statewide` (id 11, MA-wide). Plus `Investigations` (6), `Policy` (7).
- **Topic tags:** Special Education (12), Public Records (13), Funding (14),
  Transparency (15).
- **Comments are disabled site-wide** (default status closed, pattern removed
  from single templates, default test comment deleted).

## Articles — written, kept as DRAFTS (user's choice; publish from wp-admin)

Three complete long-form articles (76–80K chars each, deeply sourced) exist as
drafts. Source markdown in `C:/Users/paren/Development/sped news/`:
- **id 17** — Hellman v. Craven (SCOTUS cert, special-ed placement, Pierce v.
  Society of Sisters / unconstitutional-conditions). → District Reports +
  Investigations.
- **id 16** — Student Opportunity Act unintended consequences (New Bedford,
  funding formula). → Statewide + Policy + Funding.
- **id 15** — DESE Significant-Disproportionality memo SY2026-2027-2 (cell size
  6→10). → Statewide + Policy + Special Education.

Posts 19, 20 are throwaway test drafts (Skill Demo / Skill Test) — candidates
to delete. Post 1 is the default "Hello world!" placeholder.

## Scraper data (separate project)

`C:/Users/paren/Development/Scrapers` — MA district meeting scraper.
`data/meetings.db`, `meetings_final.jsonl`, `districts.csv`. Stats used in the
stats strip: **445 districts, 251 meetings (all with agendas), 31 with minutes,
span 2025–2027**. These are hardcoded in `patterns/record-stats.php` — update
them as the scrape grows.

## Verification done this session

Live site confirmed: hero (logo + dripping records, animated), stats strip,
docket, single-post (byline fixed to "Parent Data Force", comments removed),
404 fault scene. All screenshots in `~/OMP-Screenshots/`.

## Known gotchas

- PHP isn't installed locally — validate patterns by block-comment balance +
  careful review before deploy. A fatal in functions.php would white-screen the
  live site; deploy is reversible via git + re-deploy.
- The browser relay (user's Chrome) is flaky. Reliable render path: start
  headless Chrome (`--remote-debugging-port=9223`, fresh `--user-data-dir`) and
  attach via `browser.open({ app: { cdp_url } })`. Kill stale headless/MCP
  chrome processes if it hangs.
- `\u2019` does NOT work in PHP single-quoted strings — use the literal ’ char.

## Suggested next steps

1. User: rotate FTP password, update credentials.json, force-push, (opt) private.
2. Publish the 3 articles (wp-admin) when ready — docket/featured/single views
   will populate.
3. Build the district-browser as a real page tied to live scraper output
   (currently a design in `designs/003`+ / `scratch/articles-mock.html`).
4. Consider a district taxonomy if per-district articles grow (445 districts).
