#!/usr/bin/env python3
"""Delete theme style-variation files from the live server that no longer exist
locally.

`deploy_theme.py` only uploads; it never removes. When the stock Twenty
Twenty-Five style variations (styles/0*.json, styles/colors/,
styles/typography/) are removed from the repo, they linger live and keep
showing up in Site Editor -> Styles. This walks the remote theme's styles/
directory over FTP and deletes any .json that has no local counterpart.

Usage (run from tools/):

    python prune_theme_styles.py           # report what would be deleted
    python prune_theme_styles.py --delete  # actually delete

Stdlib only. Credentials come from ../rest/credentials.json.
"""
import ftplib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOCAL_STYLES = os.path.join(ROOT, "theme", "pdforce", "styles")
REMOTE_STYLES = "/public_html/news/wp-content/themes/pdforce/styles"
SKIP_DIRS = {"node_modules", ".git", "__pycache__"}


def load_ftp():
    with open(os.path.join(ROOT, "rest", "credentials.json"), encoding="utf-8") as f:
        c = json.load(f)["ftp"]
    ftp = ftplib.FTP(c["host"], timeout=45)
    ftp.login(c["user"], c["password"])
    return ftp




def local_json_names(root):
    names = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(".json"):
                names.add(fn)
    return names


def remote_json_files(ftp, remote_dir):
    """Every .json under a remote dir, recursively. This host's MLSD refuses
    subpaths ('550 Can't check for file existence'), so recurse on NLST."""
    found = []
    for name in sorted(ftp.nlst(remote_dir)):
        base = name.rstrip("/").rsplit("/", 1)[-1]
        if base in (".", "..", ""):
            continue
        path = "%s/%s" % (remote_dir, base)
        try:
            ftp.size(path)  # SIZE only answers for a plain file
        except Exception:
            found.extend(remote_json_files(ftp, path))
            continue
        if base.endswith(".json"):
            found.append(path)
    return found


def main():
    delete = "--delete" in sys.argv
    ftp = load_ftp()
    local = local_json_names(LOCAL_STYLES)
    remote = remote_json_files(ftp, REMOTE_STYLES)
    stale = [p for p in remote if p.rsplit("/", 1)[-1] not in local]

    for path in stale:
        print(("del " if delete else "would delete ") + path)
    if delete:
        for path in stale:
            ftp.delete(path)
    ftp.quit()
    print("%d stale file(s) %s" % (len(stale), "deleted" if delete else "found"))


if __name__ == "__main__":
    main()