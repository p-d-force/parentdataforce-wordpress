#!/usr/bin/env python3
"""Download a single WordPress theme dir over FTP (resume-capable)."""
import ftplib, os, sys, json

# Load credentials
with open("../rest/credentials.json") as f:
    creds = json.load(f)
ftp_creds = creds["ftp"]
HOST, USER, PASS = ftp_creds["host"], ftp_creds["user"], ftp_creds["password"]

SRC = "/public_html/wordpress/wp-content/themes/twentytwentyfive"
DEST = "../theme/twentytwentyfive"

ftp = ftplib.FTP(HOST); ftp.login(USER, PASS)
count = 0; errors = 0

def fetch(dirpath):
    global count, errors
    rel = dirpath.replace("/public_html/wordpress/wp-content/themes/", "")
    local = os.path.join(DEST, rel)
    os.makedirs(local, exist_ok=True)
    entries = list(ftp.mlsd(dirpath))
    dirs, files = [], []
    for name, attrs in entries:
        if name in (".", ".."):
            continue
        if attrs.get("type") == "dir":
            dirs.append(name)
        elif attrs.get("type") == "file":
            files.append((name, attrs))
    for fn, attrs in files:
        local_file = os.path.join(local, fn)
        fsz = attrs.get("size")
        if fsz and os.path.exists(local_file) and os.path.getsize(local_file) == int(fsz):
            continue
        try:
            with open(local_file, "wb") as f:
                ftp.retrbinary(f"RETR {dirpath}/{fn}", f.write)
            count += 1
        except Exception as e:
            errors += 1
            print(f"  ERR {dirpath}/{fn}: {e}")
    for d in dirs:
        fetch(f"{dirpath}/{d}")

print(f"Fetching {SRC} -> {DEST}")
fetch(SRC)
ftp.quit()
print(f"Done: {count} downloaded, {errors} errors")
