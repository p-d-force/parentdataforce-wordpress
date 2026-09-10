#!/usr/bin/env python3
"""Patch pdforce theme.json to match the live Parent Data Force site."""
import json

with open("theme.json", encoding="utf-8") as f:
    tj = json.load(f)

# --- Global color palette: dark surface + orange accent (from live site CSS) ---
tj["settings"]["color"]["palette"] = [
    {"color": "#0b0b0b", "name": "Base", "slug": "base"},
    {"color": "#f5f5f5", "name": "Contrast", "slug": "contrast"},
    {"color": "#ff5a1f", "name": "Accent 1", "slug": "accent-1"},   # orange
    {"color": "#ffa366", "name": "Accent 2", "slug": "accent-2"},   # glow
    {"color": "#161616", "name": "Accent 3", "slug": "accent-3"},   # surface
    {"color": "#a0a0a0", "name": "Accent 4", "slug": "accent-4"},   # secondary text
    {"color": "#2a2a2a", "name": "Accent 5", "slug": "accent-5"},   # border
    {"color": "#1d1d1d", "name": "Accent 6", "slug": "accent-6"},   # elevated
]

# --- Fonts: Inter (body) + JetBrains Mono (accents/code), loaded from Google Fonts ---
tj["settings"]["typography"]["fontFamilies"] = [
    {
        "name": "Inter",
        "slug": "inter",
        "fontFamily": "Inter, sans-serif",
        "fontFace": [{
            "src": ["https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800"],
            "fontWeight": "200 800",
            "fontStyle": "normal",
            "fontFamily": "Inter",
        }],
    },
    {
        "name": "JetBrains Mono",
        "slug": "jetbrains-mono",
        "fontFamily": "'JetBrains Mono', monospace",
        "fontFace": [{
            "src": ["https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500"],
            "fontWeight": "300 700",
            "fontStyle": "normal",
            "fontFamily": "'JetBrains Mono'",
        }],
    },
]

# --- Global styles ---
tj["styles"]["color"] = {"background": "#0b0b0b", "text": "#f5f5f5"}
tj["styles"]["typography"] = {
    "fontFamily": "var:preset|font-family|inter",
    "fontSize": "var:preset|font-size|large",
    "fontWeight": "400",
    "lineHeight": "1.5",
}

# Code blocks -> JetBrains Mono
tj["styles"]["blocks"]["core/code"]["typography"] = {
    "fontFamily": "var:preset|font-family|jetbrains-mono",
    "fontSize": "var:preset|font-size|medium",
    "fontWeight": "400",
}
tj["styles"]["blocks"]["core/code"]["color"] = {
    "background": "#161616",
    "text": "#f5f5f5",
}

# Buttons -> orange accent (matches live site)
tj["styles"]["elements"]["button"]["color"] = {
    "background": "var:preset|color|accent-1",
    "text": "#ffffff",
}
tj["styles"]["elements"]["button"][":hover"]["color"] = {
    "background": "#ff3b1f",
    "text": "#ffffff",
}

# Site title / links (site-title is a block, not an element)
tj["styles"]["blocks"]["core/site-title"]["typography"] = {
    "fontWeight": "700", "letterSpacing": "-0.5px", "textTransform": "uppercase",
}
tj["styles"]["blocks"]["core/site-tagline"]["color"] = {"text": "#a0a0a0"}
tj["styles"]["elements"]["link"]["color"] = {"text": "var:preset|color|accent-1"}
tj["styles"]["elements"]["link"][":hover"]["color"] = {"text": "#ffa366"}

with open("theme.json", "w", encoding="utf-8") as f:
    json.dump(tj, f, indent="\t", ensure_ascii=False)
    f.write("\n")
print("theme.json patched")
