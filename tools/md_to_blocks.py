#!/usr/bin/env python3
"""Convert the long-form Markdown articles to Gutenberg block HTML.

Pure stdlib. Supports exactly the subset used by the "sped news" articles:
  - Line 1 `# Title`            -> post title (removed from body)
  - First fully-italic line     -> dek paragraph (is-style-text-subtitle)
  - `## H2` / `### H3`         -> core/heading
  - Paragraphs                  -> core/paragraph
  - `---`                       -> core/separator (is-style-wide)
  - `- item` / `1. item`        -> core/list
  - `![alt|Caption](url)`       -> core/image -> <figure class="wp-block-image">
                                  + optional <figcaption class="wp-element-caption">
                                  ("|" splits alt from caption; caption supports
                                  inline bold/italic; url on its own line)
  - Inline **bold** / *italic*  -> <strong> / <em>
  - Inline [text](url)          -> <a href> (used sparingly, e.g. linking
                                  articles to the project page)

Usage:
  python md_to_blocks.py <article.md>           # print body block HTML
  python md_to_blocks.py <article.md> --title   # print extracted title only
"""
import re
import sys

H_RE = re.compile(r"^(#{2,3})\s+(.*)$")
HR_RE = re.compile(r"^---+$")
UL_RE = re.compile(r"^-\s+(.*)$")
OL_RE = re.compile(r"^\d+\.\s+(.*)$")
IMG_RE = re.compile(r"^!\[([^\]]*)\]\(([^()\s]+)\)$")


def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(text):
    """Escape, then links, then bold before italic so ** never misfires as two *."""
    t = escape(text)
    t = re.sub(r"\[([^\]]+)\]\(([^()\s]+)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*([^*\n]+)\*", r"<em>\1</em>", t)
    return t


def slugify(title):
    s = title.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def convert(md_text):
    """Return (title, dek_html_or_None, body_html)."""
    lines = md_text.splitlines()

    title = None
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("# "):
            title = line[2:].strip()
        break

    rest = lines[i + 1 :] if title else lines

    # Optional dek: first non-blank line fully wrapped in single asterisks.
    dek = None
    j = 0
    while j < len(rest) and not rest[j].strip():
        j += 1
    if j < len(rest):
        m = re.fullmatch(r"\*([^*].*?)\*", rest[j].strip())
        if m:
            dek = (
                '<!-- wp:paragraph {"className":"is-style-text-subtitle"} -->\n'
                f"<p class=\"is-style-text-subtitle\"><em>{inline(m.group(1))}</em></p>\n"
                "<!-- /wp:paragraph -->"
            )
            rest = rest[j + 1 :]

    out = [dek] if dek else []
    para = []

    def flush_para():
        if para:
            out.append("<!-- wp:paragraph -->\n<p>" + inline(" ".join(para)) + "</p>\n<!-- /wp:paragraph -->")
            para.clear()

    def flush_list(items, ordered):
        if not items:
            return
        tag = "ol" if ordered else "ul"
        attrs = ' {"ordered":true}' if ordered else ""
        lis = "".join(
            "<!-- wp:list-item -->\n"
            f"<li>{inline(it)}</li>\n"
            "<!-- /wp:list-item -->"
            for it in items
        )
        out.append(
            f"<!-- wp:list{attrs} -->\n<{tag} class=\"wp-block-list\">{lis}</{tag}>\n<!-- /wp:list -->"
        )
        items.clear()

    list_items, list_ordered = [], None
    k = 0
    while k < len(rest):
        raw = rest[k]
        line = raw.strip()

        ul, ol = UL_RE.match(line), OL_RE.match(line)
        if ul or ol:
            ordered = bool(ol)
            if list_items is not None and list_ordered != ordered:
                flush_list(list_items, list_ordered)
            if list_items is None:
                list_items = []
            list_ordered = ordered
            flush_para()
            list_items.append((ul or ol).group(1))
            k += 1
            continue
        if list_items is not None:
            flush_list(list_items, list_ordered)
            list_items, list_ordered = None, None

        if not line:
            flush_para()
            k += 1
            continue

        if HR_RE.match(line):
            flush_para()
            out.append(
                '<!-- wp:separator {"className":"is-style-wide"} -->\n'
                '<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>\n'
                "<!-- /wp:separator -->"
            )
            k += 1
            continue

        h = H_RE.match(line)
        if h:
            flush_para()
            level = len(h.group(1))
            out.append(
                "<!-- wp:heading -->\n"
                f'<h{level} class="wp-block-heading">{inline(h.group(2))}</h{level}>\n'
                "<!-- /wp:heading -->"
            )
            k += 1
            continue

        img = IMG_RE.match(line)
        if img:
            flush_para()
            alt, url = img.group(1), img.group(2)
            caption = None
            if "|" in alt:
                alt, caption = alt.split("|", 1)
            fig = f'<figure class="wp-block-image"><img src="{escape(url)}" alt="{escape(alt)}"/>'
            if caption:
                fig += f'<figcaption class="wp-element-caption">{inline(caption)}</figcaption>'
            fig += "</figure>"
            out.append(f"<!-- wp:image -->\n{fig}\n<!-- /wp:image -->")
            k += 1
            continue

        para.append(line)
        k += 1

    flush_para()
    if list_items is not None:
        flush_list(list_items, list_ordered)

    return title, dek, "\n\n".join(out)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    with open(sys.argv[1], encoding="utf-8") as f:
        md = f.read()
    title, _dek, body = convert(md)
    if "--title" in sys.argv:
        print(title)
    else:
        print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
