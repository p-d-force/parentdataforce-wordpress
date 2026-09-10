# Parent Data Force WordPress Site

Source of truth and deployment tooling for the Parent Data Force news site at
https://www.parentdataforce.com/news/.

The site runs a custom block theme (`pdforce`) deployed to a cPanel host over FTP,
with content published through the WordPress REST API.

**For AI assistants and contributors: read [`AGENTS.md`](AGENTS.md) first.** It documents
the architecture, the command reference split by safety, the code conventions, and the
verification procedure. This file is the short orientation.

> **Warning:** this repo deploys directly to production. There is no staging environment.

## Structure

| Path | Purpose |
|---|---|
| `theme/pdforce/` | The live block theme. Deployed wholesale. |
| `tools/` | Current Python tooling. Stdlib only. |
| `rest/` | REST CLI (`wp.py`), credentials, one-shot PHP helpers, `.htaccess` rules. |
| `docs/` | Historical planning and migration material. See caveats in `AGENTS.md`. |
| `captures/` | Frozen snapshots of the rendered site. Historical; do not edit. |

## Deployment

1. Make theme changes in `theme/pdforce/`.
2. Deploy and verify with `tools/deploy_theme.py`:

   ```bash
   cd tools
   python deploy_theme.py            # upload theme, switch theme, flush permalinks, verify
   python deploy_theme.py --verify   # verification only; writes nothing
   ```

3. Mirror the live install for offline inspection with `tools/wp_mirror.py`.

`tools/upload_theme.py` is a legacy script that uploads a fixed five-file list. Prefer
`deploy_theme.py`, which uploads the whole theme recursively and also repairs the
permalink structure.

`tools/fetch_theme.py` pulls the live theme **into** `theme/pdforce/`, overwriting local
files. Commit before running it.

## Content

Articles are authored as Markdown outside this repo and converted to Gutenberg blocks:

```bash
cd tools
python md_to_blocks.py "<path-to-article>.md"            # print block HTML
python publish_articles.py --verify                      # create drafts + verify round-trip
```

Posts are created as **drafts** assigned the `single-long-form` template. Drafts are not
publicly visible until published in wp-admin.

REST queries go through `rest/wp.py` (run from `rest/`):

```bash
python wp.py whoami
python wp.py posts --limit 10
python wp.py new-post --title "…" --content "…" --status draft
```

## Credentials

Credentials live in `rest/credentials.json` (gitignored). Never commit secrets.

The file carries `username`, `application_password`, and `rest_url` for REST Basic auth,
plus a nested `ftp` object (`host`, `user`, `password`) for deployment. Note that
`login_password` is stale: wp-login.php rejects it, so cookie-based wp-admin previews of
drafts do not work. REST access is unaffected.

## Security Notes

- Never commit passwords or API keys. `credentials.json` is untracked; verify with
  `git ls-files | grep credentials` before pushing.
- `_setpw.php` requires the `WP_NEW_PW` environment variable.
- `_fixpermalinks.php` requires a secret query parameter substituted at upload time, and
  **must be deleted from the server immediately after use**. `deploy_theme.py` does this
  and confirms a 404. If a run aborts, delete
  `/public_html/news/_fixpermalinks.php` manually.
- All scripts read credentials from the centralized `credentials.json`.

## Testing

There is no test suite and no CI. Verification is end-to-end against production: deploy,
then assert on the rendered HTML of a live URL. See the smoke-test procedure and the known
failure modes in [`AGENTS.md`](AGENTS.md#testing--qa).

## CSS Build

Only needed when editing `theme/pdforce/style.css`:

```bash
cd theme/pdforce
npm install
npm run build      # style.css -> style.min.css
```

Production enqueues `style.min.css` (it serves `style.css` only when `SCRIPT_DEBUG` is on),
so editing `style.css` without rebuilding has no visible effect.
