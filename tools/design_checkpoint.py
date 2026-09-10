#!/usr/bin/env python3
"""
Snapshot the current design artifacts into designs/<NNN>-<label>/ as a
restorable checkpoint.

Copies the live design outputs (crack vector, animated logo, ASCII raster +
path, hero engine, design mock) plus a manifest with a timestamp and note, so
every iteration of the brand/hero work is recoverable and we never lose a
good version to an overwrite.

Usage:
  python tools/design_checkpoint.py <label> ["note..."]
  e.g. python tools/design_checkpoint.py spherical-logo "spherical disc + texture"
"""
import json
import os
import shutil
import sys
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DESIGNS = os.path.join(ROOT, "designs")

# artifact path (relative to ROOT) -> kept filename
ARTIFACTS = {
    "theme/pdforce/assets/images/bolt.svg": "bolt.svg",
    "theme/pdforce/assets/images/logo-animated.svg": "logo-animated.svg",
    "theme/pdforce/assets/js/bolt-ascii.js": "bolt-ascii.js",
    "theme/pdforce/assets/js/bolt-path.js": "bolt-path.js",
    "theme/pdforce/assets/js/pdforce-ascii.js": "pdforce-ascii.js",
    "scratch/design-mock-inline.html": "design-mock.html",
    "scratch/articles-mock-inline.html": "articles-mock.html",
    "scratch/article-mock-inline.html": "article-single-mock.html",
}


def next_index():
    os.makedirs(DESIGNS, exist_ok=True)
    existing = [d for d in os.listdir(DESIGNS) if d[:3].isdigit()]
    return (max([int(d[:3]) for d in existing]) + 1) if existing else 1


def main():
    if len(sys.argv) < 2:
        print("usage: design_checkpoint.py <label> [\"note\"]"); sys.exit(1)
    label = sys.argv[1].lower().replace(" ", "-")
    note = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
    idx = next_index()
    dest = os.path.join(DESIGNS, f"{idx:03d}-{label}")
    os.makedirs(dest, exist_ok=True)

    copied = []
    for rel, name in ARTIFACTS.items():
        src = os.path.join(ROOT, rel)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dest, name))
            copied.append(name)

    manifest = {
        "checkpoint": idx,
        "label": label,
        "note": note,
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "files": copied,
    }
    with open(os.path.join(dest, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"checkpoint {idx:03d}-{label}: {len(copied)} files -> {dest}")
    for c in copied:
        print("  ", c)


if __name__ == "__main__":
    main()
