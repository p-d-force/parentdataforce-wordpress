#!/usr/bin/env python3
"""Upload the patched theme files to the live WordPress theme."""
import ftplib, os, json

# Load credentials
with open("../rest/credentials.json") as f:
    creds = json.load(f)
ftp_creds = creds["ftp"]
HOST, USER, PASS = ftp_creds["host"], ftp_creds["user"], ftp_creds["password"]

LOCAL = ".."
# (local_file, remote_ftp_path, size_hint_bytes)
items = [
    ("theme/twentytwentyfive/theme.json", "/public_html/wordpress/wp-content/themes/twentytwentyfive/theme.json"),
    ("theme/twentytwentyfive/patterns/header.php", "/public_html/wordpress/wp-content/themes/twentytwentyfive/patterns/header.php"),
    ("captures/live_logo.png", "/public_html/wordpress/wp-content/uploads/brand/logo.png"),
]
ftp = ftplib.FTP(HOST); ftp.login(USER, PASS)
for _d in ["/public_html/wordpress/wp-content/uploads/brand", "/public_html/wordpress/wp-content/uploads"]:
    try: ftp.mkd(_d)
    except Exception: pass
for local, remote in items:
    path = os.path.join(LOCAL, local)
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        ftp.storbinary(f"STOR {remote}", f)
    print(f"uploaded {local:24} -> {remote}  ({size} bytes)")
ftp.quit()
print("done")
