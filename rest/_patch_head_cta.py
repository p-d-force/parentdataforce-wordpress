#!/usr/bin/env python3
"""One-off FTP patch: insert cta-events.js <script> into /public_html/includes/head.php.

Flow: RETR head.php -> sanity checks -> STOR backup -> patch -> STOR -> MLSD confirm.
Stdlib only; creds from ../rest/credentials.json (["ftp"]).
"""
import ftplib, io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REMOTE = "/public_html/includes/head.php"
BACKUP = "/public_html/includes/head.php.bak-20260923-cta"
TAG = '<script defer src="https://www.parentdataforce.com/news/wp-content/themes/pdforce/assets/js/cta-events.js?ver=1.9"></script>'

with open(os.path.join(ROOT, "rest", "credentials.json"), encoding="utf-8") as f:
    ftp_creds = json.load(f)["ftp"]

ftp = ftplib.FTP(ftp_creds["host"], ftp_creds["user"], ftp_creds["password"])
try:
    buf = io.BytesIO()
    ftp.retrbinary(f"RETR {REMOTE}", buf.write)
    current = buf.getvalue()
    text = current.decode("utf-8")
    print(f"fetched {REMOTE}: {len(current)} bytes")

    # Sanity checks
    n_head_close = text.count("</head>")
    n_gtag = text.count("googletagmanager.com/gtag/js")
    n_cta = text.count("cta-events.js")
    print(f"checks: </head> x{n_head_close}, gtag/js x{n_gtag}, cta-events.js x{n_cta}")
    assert n_head_close == 1, "expected exactly one </head>"
    assert n_gtag == 1, "expected exactly one gtag/js loader"
    assert n_cta == 0, "cta-events.js already present - aborting"

    # Backup current bytes
    ftp.storbinary(f"STOR {BACKUP}", io.BytesIO(current))
    print(f"backup written: {BACKUP} ({len(current)} bytes)")

    # Insert before </head>, 4-space indent, single line
    idx = text.index("</head>")
    patched = text[:idx] + "    " + TAG + "\n" + text[idx:]
    ftp.storbinary(f"STOR {REMOTE}", io.BytesIO(patched.encode("utf-8")))
    print(f"patched {REMOTE}: {len(current)} -> {len(patched)} bytes")

    # Confirm listing
    names = []
    ftp.retrlines(f"MLSD /public_html/includes", names.append)
    for n in names:
        if "head.php" in n:
            print("remote entry:", n)
finally:
    ftp.quit()
print("OK")
