#!/usr/bin/env python3
"""Thin REST client for tools/: reuses rest/wp.py's WP class, adds quiet calls."""
import importlib.util
import json
import os
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REST_DIR = os.path.normpath(os.path.join(HERE, "..", "rest"))


def _load_wp_module():
    spec = importlib.util.spec_from_file_location("wp_rest", os.path.join(REST_DIR, "wp.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Client:
    def __init__(self, creds):
        self._wp = _load_wp_module().WP(creds)

    def call(self, method, path, data=None, quiet=False):
        url = self._wp.base + path
        body = json.dumps(data).encode() if data is not None else None
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", self._wp.auth)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                raw, code = r.read().decode(), r.getcode()
        except urllib.error.HTTPError as e:
            raw, code = e.read().decode(), e.code
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            obj = raw
        if code >= 400:
            print(f"[HTTP {code}] {raw[:2000]}", file=sys.stderr)
            sys.exit(code)
        if not quiet:
            print(json.dumps(obj, ensure_ascii=False, indent=2))
        return obj


    def upload_media(self, filename, data, content_type="application/pdf", quiet=True):
        """POST /wp/v2/media as multipart/form-data (call() is JSON-only).

        filename: destination filename in the media library.
        data: raw file bytes.
        Returns the attachment dict (source_url etc.). Same error behavior
        as call(): HTTP >= 400 prints the body and exits with the code.
        """
        boundary = "pdmultipart"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode("utf-8") + data + f"\r\n--{boundary}--\r\n".encode("utf-8")
        req = urllib.request.Request(self._wp.base + "/wp/v2/media", data=body, method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        req.add_header("Authorization", self._wp.auth)
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                raw, code = r.read().decode(), r.getcode()
        except urllib.error.HTTPError as e:
            raw, code = e.read().decode(), e.code
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            obj = raw
        if code >= 400:
            print(f"[HTTP {code}] {raw[:2000]}", file=sys.stderr)
            sys.exit(code)
        if not quiet:
            print(json.dumps(obj, ensure_ascii=False, indent=2))
        return obj


def client():
    with open(os.path.join(REST_DIR, "credentials.json"), encoding="utf-8") as f:
        return Client(json.load(f))
