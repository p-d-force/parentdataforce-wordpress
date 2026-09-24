#!/usr/bin/env python3
"""
Deploy the full pdforce theme to the live site over FTP.

Syncs theme/pdforce/ -> /public_html/news/wp-content/themes/pdforce/,
uploading PHP templates/patterns, the design CSS, the ASCII engine, the crack
path data, and the logo assets. Skips build/dev files that don't belong on the
server (node_modules, package files, editor styles sources, .map, etc.).

Credentials come from rest/credentials.json (gitignored). Never commit secrets.

Usage:
  python tools/deploy_theme.py            # upload changed theme files
  python tools/deploy_theme.py --dry-run  # list what would be uploaded
  python tools/deploy_theme.py --verify   # dual-plane GA + theme checks, no upload
"""
import base64
import ftplib
import json
import os
import sys
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOCAL_THEME = os.path.join(ROOT, "theme", "pdforce")
REMOTE_THEME = "/public_html/news/wp-content/themes/pdforce"

# Never upload these.
SKIP_DIRS = {"node_modules", ".git", "__pycache__"}
SKIP_FILES = {"package.json", "package-lock.json", ".DS_Store", "Thumbs.db"}
SKIP_EXT = {".map", ".log"}


def load_ftp():
    with open(os.path.join(ROOT, "rest", "credentials.json"), encoding="utf-8") as f:
        c = json.load(f)["ftp"]
    ftp = ftplib.FTP(c["host"], timeout=45)
    ftp.login(c["user"], c["password"])
    return ftp


def ensure_dir(ftp, path):
    """mkdir -p for FTP: walk the path creating each segment."""
    parts = [p for p in path.split("/") if p]
    cur = ""
    for p in parts:
        cur += "/" + p
        try:
            ftp.mkd(cur)
        except Exception:
            pass  # already exists


def collect():
    files = []
    for dirpath, dirnames, filenames in os.walk(LOCAL_THEME):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn in SKIP_FILES or os.path.splitext(fn)[1] in SKIP_EXT:
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, LOCAL_THEME).replace(os.sep, "/")
            files.append((full, REMOTE_THEME + "/" + rel))
    return files


BASE_URL = "https://www.parentdataforce.com"
GA_ID = "G-BVQTKPYBG2"
REST_QUERY = "/wp-json/wp/v2/posts?per_page=1&status=publish&_fields=id,link"


def http_get(url, auth=None):
    """GET url, follow redirects, return (status, body). HTTPError -> (code, body)."""
    headers = {"User-Agent": "pdforce-deploy-verify/1.0"}
    if auth:
        headers["Authorization"] = "Basic " + auth
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def latest_post_url():
    """Public REST: newest published post's permalink. Raises on failure."""
    status, body = http_get(BASE_URL + REST_QUERY)
    if status in (401, 403):
        with open(os.path.join(ROOT, "rest", "credentials.json"), encoding="utf-8") as f:
            creds = json.load(f)
        token = base64.b64encode(
            f"{creds['username']}:{creds['application_password']}".encode()
        ).decode()
        status, body = http_get(BASE_URL + REST_QUERY, auth=token)
    if status != 200:
        raise RuntimeError(f"REST posts returned HTTP {status}")
    posts = json.loads(body)
    if not posts:
        raise RuntimeError("REST posts returned no published posts")
    return posts[0]["link"]


def verify():
    failures = []
    # Static pages get GA via /public_html/includes/head.php; only the GA marker applies.
    static_required = [GA_ID]
    # WP-served pages render the theme (body class) and inherit the GA hook.
    wp_required = [GA_ID, "wp-theme-pdforce"]
    try:
        latest = latest_post_url()
    except Exception as exc:  # REST failure surfaces as a check failure, never a traceback
        failures.append(f"latest-post: {exc}")
        latest = None
    urls = [
        ("home", BASE_URL + "/", wp_required),
        ("donate", BASE_URL + "/donate/", wp_required),
        ("about", BASE_URL + "/about/", static_required),
        ("projects", BASE_URL + "/projects/", static_required),
    ]
    if latest:
        urls.insert(1, ("latest-post", latest, wp_required))
    for label, url, required in urls:
        status, body = http_get(url)
        missing = [m for m in required if m not in body]
        if status != 200 or missing:
            failures.append(f"{label} ({url}): HTTP {status}, missing {missing}")
        else:
            print(f"  {label}: OK ({url})")
    print("verify: all checks passed" if not failures else "verify: FAILED")
    for f in failures:
        print("  FAIL", f)
    return not failures


def main():
    force = "--all" in sys.argv
    dry = "--dry-run" in sys.argv
    files = collect()
    print(f"{len(files)} theme files to consider")
    if dry:
        for _, r in files:
            print("  ", r)
        return
    ftp = load_ftp()
    dirs = sorted({os.path.dirname(r) for _, r in files})
    for d in dirs:
        ensure_dir(ftp, d)
    up = skip = 0
    for local, remote in files:
        size = os.path.getsize(local)
        if not force:
            try:
                if ftp.size(remote) == size:
                    skip += 1
                    continue
            except Exception:
                pass  # not on server yet -> upload
        with open(local, "rb") as f:
            ftp.storbinary(f"STOR {remote}", f)
        up += 1
        print(f"  up {size:>8}  {remote}")
    ftp.quit()
    print(f"done: {up} uploaded, {skip} unchanged")


if __name__ == "__main__":
    if "--verify" in sys.argv:
        sys.exit(0 if verify() else 1)
    main()
