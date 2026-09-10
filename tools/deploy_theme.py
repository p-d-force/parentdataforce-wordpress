#!/usr/bin/env python3
"""Deploy the pdforce theme to the live server and fix permalinks.

Steps:
  1. Recursively upload theme/pdforce/ to /public_html/news/wp-content/themes/pdforce/
     over FTP (resume-capable: skips files whose remote size matches local).
  2. Upload rest/_fixpermalinks.php with a random secret substituted, invoke it
     once over HTTPS to switch_theme('pdforce') + set permalink_structure=/%postname%/
     + flush rewrite rules, then DELETE it from the server.
  3. Verify: active theme over REST, plus unauthenticated GETs of the home page
     and a known post URL.

Usage:
  python deploy_theme.py              # full deploy + verify
  python deploy_theme.py --upload     # upload only
  python deploy_theme.py --fix        # permalink/theme helper only
  python deploy_theme.py --verify     # verification only
"""
import ftplib
import io
import json
import os
import re
import secrets
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)  # scripts in tools/ resolve ../rest relative to cwd

with open("../rest/credentials.json", encoding="utf-8") as f:
    creds = json.load(f)
FTP = creds["ftp"]
HOST, USER, PASS = FTP["host"], FTP["user"], FTP["password"]

THEME_LOCAL = os.path.normpath("../theme/pdforce")
THEME_REMOTE = "/public_html/news/wp-content/themes/pdforce"
WP_ROOT = "/public_html/news"
SITE = "https://www.parentdataforce.com/news"


def connect():
    ftp = ftplib.FTP(HOST, timeout=120)
    ftp.login(USER, PASS)
    ftp.set_pasv(True)
    return ftp


def remote_sizes(ftp, path):
    try:
        return {n: int(a.get("size", -1)) for n, a in ftp.mlsd(path) if a.get("type") == "file"}
    except ftplib.error_perm:
        return None  # dir does not exist


def upload_tree(ftp):
    uploaded = skipped = errors = 0
    stack = [(THEME_LOCAL, THEME_REMOTE)]
    while stack:
        local_dir, remote_dir = stack.pop()
        sizes = remote_sizes(ftp, remote_dir)
        if sizes is None:
            try:
                ftp.mkd(remote_dir)
            except ftplib.error_perm:
                pass
            sizes = {}
        for name in sorted(os.listdir(local_dir)):
            lp = os.path.join(local_dir, name)
            rp = remote_dir + "/" + name
            if os.path.isdir(lp):
                stack.append((lp, rp))
                continue
            lsz = os.path.getsize(lp)
            if sizes.get(name) == lsz:
                skipped += 1
                continue
            for attempt in range(3):
                try:
                    with open(lp, "rb") as fh:
                        ftp.storbinary(f"STOR {rp}", fh)
                    uploaded += 1
                    break
                except (ftplib.error_temp, OSError, EOFError) as e:
                    if attempt == 2:
                        errors += 1
                        print(f"  ERR {rp}: {e}")
                    else:
                        try:
                            ftp.voidcmd("NOOP")
                        except Exception:
                            ftp = connect()
    print(f"upload: {uploaded} uploaded, {skipped} skipped (size match), {errors} errors")
    return ftp


def run_helper(ftp):
    secret = secrets.token_urlsafe(24)
    with open("../rest/_fixpermalinks.php", encoding="utf-8") as f:
        php = f.read().replace("__SECRET__", secret)
    remote = WP_ROOT + "/_fixpermalinks.php"
    ftp.storbinary(f"STOR {remote}", io.BytesIO(php.encode()))
    print(f"helper uploaded to {remote}")
    try:
        url = f"{SITE}/_fixpermalinks.php?key={secret}&switch=pdforce"
        with urllib.request.urlopen(url, timeout=180) as r:
            out = json.loads(r.read().decode())
        print("helper result:", json.dumps(out, indent=1))
    finally:
        try:
            ftp.delete(remote)
            print("helper deleted from server")
        except ftplib.all_errors as e:
            print(f"WARNING: could not delete helper: {e} — DELETE {remote} MANUALLY")
    # confirm 404
    try:
        urllib.request.urlopen(f"{SITE}/_fixpermalinks.php", timeout=60)
        print("WARNING: helper still reachable!")
    except urllib.error.HTTPError as e:
        print(f"helper gone (HTTP {e.code})")


def http_check(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        r = urllib.request.urlopen(req, timeout=60)
        html = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.geturl(), ""
    return r.getcode(), r.geturl(), html


def verify():
    import wp_api
    wp = wp_api.client()
    themes = wp.call("GET", "/wp/v2/themes?status=active&_fields=stylesheet,name", quiet=True)
    print("active theme:", json.dumps(themes))
    settings = wp.call("GET", "/wp/v2/settings?_fields=title,url", quiet=True)
    print("settings:", json.dumps(settings))

    for url in (SITE + "/", SITE + "/hello-world/", SITE + "/?p=1",
                SITE + "/wp-content/uploads/brand/logo.png"):
        code, final, html = http_check(url)
        title = re.search(r"<title>(.*?)</title>", html, re.S)
        body = re.search(r"<body[^>]*class=\"([^\"]*)\"", html)
        print(f"GET {url}\n  -> {code} {final}")
        if title:
            print(f"     title: {title.group(1).strip()[:80]}")
        if body:
            print(f"     body class: {body.group(1)[:140]}")


def main():
    args = set(sys.argv[1:])
    ftp = connect()
    try:
        if not args or "--upload" in args:
            ftp = upload_tree(ftp)
        if not args or "--fix" in args:
            run_helper(ftp)
    finally:
        try:
            ftp.quit()
        except Exception:
            pass
    if not args or "--verify" in args:
        verify()


if __name__ == "__main__":
    main()
