#!/usr/bin/env python3
"""Stdlib-only text-to-PDF writer for tracker source documents.

Renders plain-text documents (sent request/appeal emails that exist only as
message bodies) as letter-size PDFs using the PDF core fonts. No third-party
dependency; page geometry 612x792 with 72pt margins, Helvetica 11pt body and
Helvetica-Bold 13pt title, cp1252 encoding under WinAnsiEncoding.

Usage (run from tools/):

    from text_pdf import write_text_pdf
    write_text_pdf(path, title, paragraphs)
"""
import os

PAGE_W, PAGE_H, MARGIN = 612.0, 792.0, 72.0
USABLE = PAGE_W - 2 * MARGIN
TITLE_SIZE, BODY_SIZE, BODY_LEAD = 13, 11, 14.5

# Helvetica / Helvetica-Bold AFM widths (per mille) for chars 32..126.
_REG = ("278 278 355 556 556 889 667 191 333 333 389 584 278 333 278 278 "
        + "556 " * 10
        + "278 278 584 584 584 556 1015 667 667 722 722 667 611 778 722 278 500 "
        "667 556 833 722 778 667 778 722 667 611 722 667 944 667 667 611 278 278 "
        "278 469 556 333 556 556 500 556 556 278 556 556 222 222 500 222 833 556 "
        "556 556 556 333 500 278 556 500 722 500 500 500 334 260 334 584")
_BOLD = ("278 333 474 556 556 889 722 238 333 333 389 584 278 333 278 278 "
         + "556 " * 10
         + "333 333 584 584 584 611 975 722 722 722 722 667 611 778 722 278 556 "
         "722 611 833 722 778 667 778 722 667 611 722 667 944 667 667 611 333 278 "
         "333 584 556 333 556 611 556 611 556 333 611 611 278 278 556 278 889 611 "
         "611 611 611 389 556 333 611 556 778 556 556 500 389 280 389 584")
_TABLES = {"F1": [int(w) for w in _REG.split()], "F2": [int(w) for w in _BOLD.split()]}
_EXTRA = {"\u2018": 222, "\u2019": 222, "\u201a": 222, "\u201c": 333, "\u201d": 333,
          "\u2013": 556, "\u2014": 1000, "\u00a7": 556, "\u2022": 350, "\u00b7": 278}


def _width(text, font, size):
    tab = _TABLES[font]
    return size * sum(
        _EXTRA.get(ch, tab[ord(ch) - 32] if 32 <= ord(ch) < 127 else 556)
        for ch in text) / 1000.0


def _wrap(text, font, size, maxw):
    lines, cur = [], ""
    for word in text.split():
        cand = (cur + " " + word).strip()
        if cur and _width(cand, font, size) > maxw:
            lines.append(cur)
            cur = word
        else:
            cur = cand
    lines.append(cur)
    return lines


def _esc(text):
    return (text.encode("cp1252", "replace")
            .replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")
            .decode("latin-1"))


def write_text_pdf(path, title, paragraphs):
    """Write title + body paragraphs as a paginated PDF at `path`."""
    # Layout: list of (font, size, text) plus None = paragraph gap.
    layout = [("F2", TITLE_SIZE, title)]
    for para in paragraphs:
        layout.append(None)
        for seg in para.split("\n"):   # \n = hard break (no gap)
            layout.extend(("F1", BODY_SIZE, ln)
                          for ln in _wrap(seg, "F1", BODY_SIZE, USABLE - 8))
    pages, page, y = [], [], PAGE_H - MARGIN
    for item in layout:
        size = item[1] if item else BODY_SIZE
        gap = item is None
        if not gap and y - size < MARGIN:          # page break
            while page and page[-1][1] is None:    # drop trailing gaps
                page.pop()
            pages.append(page)
            page, y = [], PAGE_H - MARGIN
        if gap:
            if page:
                page.append((y, None))
                y -= BODY_LEAD
            continue
        page.append((y, item))
        y -= BODY_LEAD if item[0] == "F1" else TITLE_SIZE + 5.5
    if page:
        pages.append(page)

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = {}

    def add(num, body):
        offsets[num] = len(out)
        out.extend(f"{num} 0 obj\n{body}\nendobj\n".encode("latin-1"))

    add(1, "<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{5 + 2 * i} 0 R" for i in range(len(pages)))
    add(2, f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>")
    add(3, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
           "/Encoding /WinAnsiEncoding >>")
    add(4, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold "
           "/Encoding /WinAnsiEncoding >>")
    for i, page in enumerate(pages):
        ops = []
        for y, item in page:
            if item is None:
                continue
            font, size, text = item
            ops.append(f"BT /{font} {size} Tf {MARGIN:.0f} {y:.1f} Td "
                       f"({_esc(text)}) Tj ET")
        stream = "\n".join(ops)
        add(6 + 2 * i, f"<< /Length {len(stream.encode('latin-1'))} >>\nstream\n"
                       f"{stream}\nendstream")
        add(5 + 2 * i, "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                       "/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
                       f"/Contents {6 + 2 * i} 0 R >>")
    xref_at = len(out)
    n = 5 + 2 * len(pages)
    out.extend(b"xref\n0 " + str(n).encode() + b"\n0000000000 65535 f \n")
    for num in range(1, n):
        out.extend(f"{offsets[num]:010d} 00000 n \n".encode())
    out.extend(b"trailer\n<< /Size " + str(n).encode() + b" /Root 1 0 R >>\n"
               b"startxref\n" + str(xref_at).encode() + b"\n%%EOF\n")
    with open(path, "wb") as f:
        f.write(bytes(out))
    return len(pages)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        sys.exit("usage: python text_pdf.py <out.pdf>")
    write_text_pdf(sys.argv[1], "Sample — “quoted” §10A",
                   ["First paragraph with an em dash — and $2,950 in fees.",
                    "Second paragraph wraps across several lines to exercise "
                    "the width table and pagination path of this writer."])
    print("wrote", sys.argv[1])
