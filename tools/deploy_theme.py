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
"""
import ftplib
import json
import os
import sys

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
    main()
