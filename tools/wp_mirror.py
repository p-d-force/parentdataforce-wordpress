#!/usr/bin/env python3
"""Mirror the parentdataforce.com WordPress install over FTP.

Usage: python wp_mirror.py [ftp_src] [dest]
Defaults:
  ftp_src = /public_html/news
  dest    = ../wordpress-copy
"""
import ftplib
import os
import sys
import json

# Load credentials
with open("../rest/credentials.json") as f:
    creds = json.load(f)
ftp_creds = creds["ftp"]
HOST, USER, PASS = ftp_creds["host"], ftp_creds["user"], ftp_creds["password"]

SRC = "/public_html/news"
DEST = "../wordpress-copy"

if len(sys.argv) > 1:
    SRC = sys.argv[1]
if len(sys.argv) > 2:
    DEST = sys.argv[2]

SRCNOSLASH = SRC.lstrip("/")

ftp = ftplib.FTP(HOST)
ftp.login(USER, PASS)

count = 0
errors = 0

def fetch(dirpath):
    global count, errors
    # Map an FTP dir under SRC to the mirror root + relative remainder.
    # Use lstrip("/") (remove the leading slash), NOT lstrip() (whitespace).
    rel = dirpath.lstrip("/")[len(SRCNOSLASH):].lstrip("/")
    local = os.path.join(DEST, rel)
    os.makedirs(local, exist_ok=True)

    try:
        entries = ftp.mlsd(dirpath)
        dirs, files = [], []
        for name, attrs in entries:
            # attrs is a dict; test the value, not membership of a string.
            if attrs.get("type") == "dir" and name not in (".", ".."):
                dirs.append(name)
            elif attrs.get("type") == "file":
                files.append((name, attrs))
    except ftplib.error_perm:
        # server doesn't support MLSD; fall back to nlst + cwd probe
        entries = ftp.nlst(dirpath)
        dirs, files = [], []
        for name in entries:
            if name in (".", ".."):
                continue
            try:
                ftp.cwd(f"{dirpath}/{name}")
                ftp.cwd("..")
                dirs.append(name)
            except ftplib.error_perm:
                files.append((name, None))

    for fn, attrs in files:
        local_file = os.path.join(local, fn)
        # Resume: skip files already present with a matching size (avoids re-downloading the ~3,400 plugin files).
        fsz = attrs.get("size") if attrs else None
        if fsz and os.path.exists(local_file) and os.path.getsize(local_file) == int(fsz):
            continue
        try:
            with open(local_file, "wb") as f:
                ftp.retrbinary(f"RETR {dirpath}/{fn}", f.write)
            count += 1
        except Exception as e:
            errors += 1
            print(f"  ERROR fetching {dirpath}/{fn}: {e}")

    for d in dirs:
        if d == "uploads":
            continue  # user chose core + plugins + themes, no uploads
        fetch(f"{dirpath}/{d}")

print(f"Mirroring ftp://{HOST}{SRC} -> {DEST}")
fetch(SRC)
ftp.quit()
print(f"Done: {count} files downloaded, {errors} errors")
