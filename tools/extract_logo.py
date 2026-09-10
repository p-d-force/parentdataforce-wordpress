#!/usr/bin/env python3
"""
Extract the Parent Data Force lightning bolt from the master logo PNG and emit:

  1. theme/pdforce/assets/images/bolt.svg      - traced vector path (exact shape)
  2. theme/pdforce/assets/js/bolt-ascii.js      - ASCII raster of the same mask

The bolt's silhouette is preserved exactly: the source mask is the largest
bright-warm connected component of captures/live_logo.png, hole-filled and
boundary-traced with Moore-Neighbor tracing, then simplified with
Douglas-Peucker (default tolerance keeps every jag of the original line).

No third-party tracing deps: numpy + scipy + PIL only.
"""
import os
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "captures", "live_logo.png")
SVG_OUT = os.path.join(ROOT, "theme", "pdforce", "assets", "images", "bolt.svg")
ASCII_OUT = os.path.join(ROOT, "theme", "pdforce", "assets", "js", "bolt-ascii.js")


def bolt_mask(path):
    """Full-size warm crack mask + a HARD circular disc mask (not the soft alpha
    edge), so the clipped crack can never poke past the true circle boundary."""
    im = np.array(Image.open(path).convert("RGBA")).astype(np.int32)
    r, g, b, a = im[..., 0], im[..., 1], im[..., 2], im[..., 3]
    alpha = a > 0
    dys, dxs = np.where(alpha)
    cx, cy = dxs.mean(), dys.mean()
    rr = (dxs.max() - dxs.min()) / 2.0
    yy, xx = np.mgrid[0:im.shape[0], 0:im.shape[1]]
    disc = ((xx - cx) ** 2 + (yy - cy) ** 2) <= (rr - 1.5) ** 2  # hard, 1.5px inset
    warm = (r > 150) & (r > g + 30) & (r > b + 30) & disc
    lab, n = ndimage.label(warm)
    if n == 0:
        raise SystemExit("no bolt found")
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    big = int(np.argmax(sizes)) + 1
    mask = ndimage.binary_fill_holes(lab == big)
    return mask, disc


def _pca_axis(pts):
    c = pts.mean(axis=0)
    cov = np.cov((pts - c).T)
    vals, vecs = np.linalg.eigh(cov)
    u = vecs[:, int(np.argmax(vals))]
    return c, u / np.linalg.norm(u)


def extend_crack_to_edges(mask, disc):
    """Extend the crack's two tips along the fault axis to the disc boundary,
    tapering to a point so it reads as a fissure splitting the whole disc."""
    m = mask.copy()
    ys, xs = np.where(mask)
    pts = np.column_stack([xs, ys]).astype(float)
    c, u = _pca_axis(pts)
    perp = np.array([-u[1], u[0]])
    proj = (pts - c) @ u
    prange = proj.max() - proj.min()

    dys, dxs = np.where(disc)
    dc = np.array([dxs.mean(), dys.mean()])
    dr = (dxs.max() - dxs.min()) / 2.0

    yy, xx = np.mgrid[0:mask.shape[0], 0:mask.shape[1]]

    for sgn in (1, -1):
        extreme = proj.max() if sgn > 0 else proj.min()
        band = pts[np.abs(proj - extreme) < 0.06 * prange]
        tip = band.mean(axis=0)
        width = float(((band - c) @ perp).max() - ((band - c) @ perp).min())
        out = u * sgn
        if np.dot(out, tip - c) < 0:
            out = -out
        # distance along the outward ray to the disc circle (robust to near-edge)
        v = tip - dc
        bq = float(np.dot(v, out))
        disc_term = bq * bq - (float(np.dot(v, v)) - dr * dr)
        D = (-bq + np.sqrt(disc_term)) if disc_term > 0 else 20.0
        D = D * 1.2 + 12.0  # overshoot past the edge; the disc clip trims flush
        r0 = max(1.5, width / 2.0)
        s = 0.0
        while s < D:
            p = tip + out * s
            rad = max(0.4, r0 * (1.0 - s / D))  # taper r0 -> point past edge
            cx, cy = int(round(p[0])), int(round(p[1]))
            m[((xx - cx) ** 2 + (yy - cy) ** 2) <= rad * rad] = True
            s += 1.5
    return m & disc  # clip to the disc so the crack meets the edge cleanly


def crop(mask):
    ys, xs = np.where(mask)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    return mask[y0:y1, x0:x1], (int(x0), int(y0), int(x1), int(y1))


# --- Moore-Neighbor boundary tracing (Jacob's stopping criterion) -----------
# 8-neighborhood offsets, clockwise starting from the pixel above.
_NBRS = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]


def trace_boundary(mask):
    """Ordered list of (x, y) boundary points around the mask (pixel centers)."""
    p = np.pad(mask.astype(np.uint8), 1)  # guard border
    # start: topmost-then-leftmost filled pixel
    ys, xs = np.where(p)
    start = (ys[0], xs[0])
    contour = [start]
    # backtrack direction index pointing at the previously-visited (empty) pixel
    b_dir = 6  # came from the left (0,-1) region; we enter scanning clockwise
    cur = start
    prev_back = None
    max_iter = p.size * 4
    it = 0
    while it < max_iter:
        it += 1
        found = False
        # search clockwise from the pixel after the backtrack
        for k in range(8):
            idx = (b_dir + 1 + k) % 8
            dy, dx = _NBRS[idx]
            ny, nx = cur[0] + dy, cur[1] + dx
            if p[ny, nx]:
                # record where we came FROM (the empty pixel before this one)
                pdy, pdx = _NBRS[(idx - 1) % 8]
                prev_back = (cur[0] + pdy, cur[1] + pdx)
                cur = (ny, nx)
                b_dir = (idx + 4) % 8  # new backtrack = opposite direction
                contour.append(cur)
                found = True
                break
        if not found:
            break  # isolated single pixel
        # Jacob's stop: back at start AND about to repeat the second move
        if cur == start and len(contour) > 2:
            break
    # drop padding offset, return as (x, y)
    pts = [(x - 1, y - 1) for (y, x) in contour]
    return pts


def douglas_peucker(pts, tol):
    """Iterative Douglas-Peucker on a closed polyline of (x, y)."""
    n = len(pts)
    if n < 3:
        return pts
    keep = np.ones(n, dtype=bool)
    stack = [(0, n - 1)]
    P = np.array(pts, dtype=float)
    while stack:
        i0, i1 = stack.pop()
        a, b = P[i0], P[i1]
        ab = b - a
        denom = np.hypot(ab[0], ab[1])
        if i1 - i0 < 2:
            continue
        seg = P[i0 + 1:i1]
        if denom == 0:
            d = np.hypot(seg[:, 0] - a[0], seg[:, 1] - a[1])
        else:
            # 2D cross product magnitude: |ab_x*(seg_y-a_y) - ab_y*(seg_x-a_x)|
            d = np.abs(ab[0] * (seg[:, 1] - a[1]) - ab[1] * (seg[:, 0] - a[0])) / denom
        j = int(np.argmax(d))
        if d[j] > tol:
            mid = i0 + 1 + j
            keep[mid] = True
            stack.append((i0, mid))
            stack.append((mid, i1))
        else:
            keep[i0 + 1:i1] = False
    return [pts[i] for i in range(n) if keep[i]]


def to_svg(mask, tol=1.2):
    h, w = mask.shape
    pts = trace_boundary(mask)
    simp = douglas_peucker(pts, tol)
    d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in simp) + " Z"
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}" role="img" aria-label="Parent Data Force bolt">\n'
        f'  <path d="{d}" fill="#ff5a1f"/>\n</svg>\n'
    )
    return svg, len(pts), len(simp), (w, h)


def to_ascii(mask, cols=44):
    """Rasterize mask to a monospace ASCII grid, preserving aspect (~2:1 char)."""
    h, w = mask.shape
    rows = max(1, round(cols * (h / w) * 0.5))  # 0.5 corrects char aspect
    im = Image.fromarray((mask * 255).astype(np.uint8)).resize((cols, rows), Image.LANCZOS)
    a = np.array(im) / 255.0
    ramp = " .:-=+*#%@"
    lines = []
    for r in range(rows):
        line = "".join(ramp[min(len(ramp) - 1, int(v * (len(ramp) - 1) + 0.5))] for v in a[r])
        lines.append(line.rstrip())
    # trim empty top/bottom
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def main():
    tol = float(os.environ.get("BOLT_TOL", "1.2"))
    cols = int(os.environ.get("BOLT_COLS", "44"))
    full, disc = bolt_mask(SRC)
    extended = extend_crack_to_edges(full, disc)
    mask, bbox = crop(extended)
    # report bbox so build_animated_logo.py can place the mark in the disc
    print(f"BOLT_BBOX {bbox[0]} {bbox[1]} {bbox[2]} {bbox[3]}")
    svg, raw_pts, simp_pts, (w, h) = to_svg(mask, tol)
    os.makedirs(os.path.dirname(SVG_OUT), exist_ok=True)
    with open(SVG_OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    lines = to_ascii(mask, cols)
    os.makedirs(os.path.dirname(ASCII_OUT), exist_ok=True)
    js = (
        "/* Auto-generated by tools/extract_logo.py from captures/live_logo.png.\n"
        " * Exact ASCII raster of the bolt silhouette. Do not hand-edit shape. */\n"
        "window.PDFORCE_BOLT_ASCII = " + __import__("json").dumps(lines, ensure_ascii=False) + ";\n"
    )
    with open(ASCII_OUT, "w", encoding="utf-8") as f:
        f.write(js)
    print(f"mask bbox={bbox} cropped {w}x{h}")
    print(f"contour: {raw_pts} raw -> {simp_pts} simplified (tol={tol})")
    print(f"SVG  -> {SVG_OUT}")
    print(f"ASCII {cols}x{len(lines)} -> {ASCII_OUT}")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
