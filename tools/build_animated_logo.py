#!/usr/bin/env python3
"""
Generate the animated Parent Data Force logo as a self-contained SVG.

Reads the traced crack outline from theme/pdforce/assets/images/bolt.svg
(produced by extract_logo.py) and composes it into the brand disc, faithful
to the master art:

  - black disc with a warm radial vignette
  - faint procedural hairline cracks + fine grain (the cracked-earth texture)
  - a warm ambient glow bleeding out of the fissure into the stone
  - the crack filled with the signal orange ramp (shape used verbatim)
  - a shine sweep travelling down the fissure
  - drifting ember particles

The crack group is clipped to the disc so the tips meet the edge exactly and
never overshoot. All motion is CSS, disabled under prefers-reduced-motion.
No JavaScript, no external assets.
"""
import os
import re
import math
import random

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BOLT_SVG = os.path.join(ROOT, "theme", "pdforce", "assets", "images", "bolt.svg")
OUT = os.path.join(ROOT, "theme", "pdforce", "assets", "images", "logo-animated.svg")

# Crack bbox in the 1024x1024 master (from extract_logo.py BOLT_BBOX).
BOLT_TX, BOLT_TY = 233, 155
# Source disc measured from the alpha channel of live_logo.png.
DISC_CX, DISC_CY, DISC_R = 512.8, 514.5, 457.5

# Ember particles: (cx, cy, r, dur_s, delay_s, drift_x)
EMBERS = [
    (612, 250, 3.0, 5.0, 0.0, -18), (560, 330, 2.2, 6.5, 1.2, -24),
    (650, 430, 2.6, 5.6, 2.1, -14), (430, 560, 3.2, 7.0, 0.6, 20),
    (360, 610, 2.2, 5.2, 3.0, 16),  (300, 720, 2.8, 6.2, 1.8, 22),
    (540, 700, 2.4, 5.8, 2.6, -20), (470, 780, 3.0, 6.8, 0.9, 14),
    (600, 560, 2.0, 5.4, 4.0, -12), (390, 380, 2.6, 6.0, 2.9, 18),
    (700, 300, 2.4, 6.4, 1.5, -16), (330, 480, 2.0, 5.0, 3.6, 12),
    (590, 470, 1.7, 5.5, 2.2, -10), (470, 300, 1.8, 6.1, 3.8, 14),
    (660, 620, 2.1, 5.9, 1.0, -18), (350, 700, 1.6, 5.3, 4.4, 10),
]


def hairline_cracks(seed, count):
    """Deterministic faint fissures scattered across the disc (cracked stone)."""
    rng = random.Random(seed)
    out = []
    for _ in range(count):
        ang = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0.15, 0.8) * DISC_R
        x = DISC_CX + rr * math.cos(ang)
        y = DISC_CY + rr * math.sin(ang)
        heading = rng.uniform(0, 2 * math.pi)
        d = f"M {x:.1f},{y:.1f} "
        for _ in range(rng.randint(4, 9)):
            heading += rng.uniform(-0.85, 0.85)
            ln = rng.uniform(9, 30)
            x += ln * math.cos(heading)
            y += ln * math.sin(heading)
            if (x - DISC_CX) ** 2 + (y - DISC_CY) ** 2 > (DISC_R - 10) ** 2:
                break
            d += f"L {x:.1f},{y:.1f} "
        wdt = rng.uniform(0.8, 1.6)
        op = rng.uniform(0.25, 0.5)
        out.append(f'      <path d="{d}" stroke="#241612" stroke-width="{wdt:.1f}" '
                   f'stroke-opacity="{op:.2f}" fill="none" stroke-linecap="round"/>')
    return "\n".join(out)


def branch_cracks(seed, count, bolt_pts):
    """Short fissures branching off the main fault, so it reads as cracked open."""
    rng = random.Random(seed)
    out = []
    picks = rng.sample(bolt_pts, min(count, len(bolt_pts)))
    for (bx, by) in picks:
        heading = rng.uniform(0, 2 * math.pi)
        d = f"M {bx:.1f},{by:.1f} "
        x, y = bx, by
        for _ in range(rng.randint(3, 6)):
            heading += rng.uniform(-0.7, 0.7)
            ln = rng.uniform(8, 22)
            x += ln * math.cos(heading)
            y += ln * math.sin(heading)
            if (x - DISC_CX) ** 2 + (y - DISC_CY) ** 2 > (DISC_R - 8) ** 2:
                break
            d += f"L {x:.1f},{y:.1f} "
        out.append(f'      <path d="{d}" stroke="#3a1c10" stroke-width="1.1" '
                   f'stroke-opacity="0.6" fill="none" stroke-linecap="round"/>')
    return "\n".join(out)


def bolt_sample_points(d, n=14):
    """Evenly-ish spaced points along the crack for branch origins + glow."""
    pts = re.findall(r'([0-9.]+),([0-9.]+)', d)
    xy = [(float(a) + BOLT_TX, float(b) + BOLT_TY) for a, b in pts]
    if not xy:
        return []
    step = max(1, len(xy) // n)
    return xy[::step]


def ember(cx, cy, r, dur, delay, dx):
    return (f'    <circle class="ember" cx="{cx}" cy="{cy}" r="{r}" '
            f'style="animation-duration:{dur}s;animation-delay:{delay}s;--dx:{dx}px"/>\n')


def main():
    raw = open(BOLT_SVG, encoding="utf-8").read()
    d = re.search(r'd="([^"]+)"', raw).group(1)

    embers = "".join(ember(*e) for e in EMBERS)
    samples = bolt_sample_points(d, 14)
    hairlines = hairline_cracks(seed=7, count=26)
    branches = branch_cracks(seed=21, count=16, bolt_pts=samples)
    vx, vy = DISC_CX - DISC_R, DISC_CY - DISC_R
    vs = DISC_R * 2

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vx:.1f} {vy:.1f} {vs:.1f} {vs:.1f}" width="1024" height="1024" role="img" aria-label="Parent Data Force — fault line">
  <defs>
    <path id="bolt" d="{d}" transform="translate({BOLT_TX},{BOLT_TY})"/>
    <radialGradient id="bg" cx="38%" cy="33%" r="80%">
      <stop offset="0%" stop-color="#2e1c10"/>
      <stop offset="28%" stop-color="#1a0f08"/>
      <stop offset="62%" stop-color="#100905"/>
      <stop offset="88%" stop-color="#070403"/>
      <stop offset="100%" stop-color="#030201"/>
    </radialGradient>
    <radialGradient id="spec" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#ffd9bd" stop-opacity="0.5"/>
      <stop offset="40%" stop-color="#ff9a5c" stop-opacity="0.18"/>
      <stop offset="100%" stop-color="#ff9a5c" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="limb" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#000" stop-opacity="0"/>
      <stop offset="78%" stop-color="#000" stop-opacity="0"/>
      <stop offset="94%" stop-color="#000" stop-opacity="0.45"/>
      <stop offset="100%" stop-color="#000" stop-opacity="0.7"/>
    </radialGradient>
    <radialGradient id="warmglow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#ff5a1f" stop-opacity="0.55"/>
      <stop offset="55%" stop-color="#c33d0d" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="#000" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="boltfill" x1="0" y1="0" x2="0.25" y2="1">
      <stop offset="0%" stop-color="#ffb078"/>
      <stop offset="45%" stop-color="#ff6a2b"/>
      <stop offset="100%" stop-color="#e6440a"/>
    </linearGradient>
    <linearGradient id="shine" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#fff" stop-opacity="0"/>
      <stop offset="50%" stop-color="#ffd9bd" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="boltclip"><use href="#bolt"/></clipPath>
    <clipPath id="discclip"><circle cx="{DISC_CX}" cy="{DISC_CY}" r="{DISC_R}"/></clipPath>
    <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="16" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="softblur" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="30"/>
    </filter>
    <filter id="grain">
      <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" result="n"/>
      <feColorMatrix in="n" type="matrix"
        values="0 0 0 0 0.10  0 0 0 0 0.07  0 0 0 0 0.05  0 0 0 0.5 0"/>
      <feComposite operator="in" in2="SourceGraphic"/>
    </filter>
    <style>
      .bolt-core {{ fill: url(#boltfill); }}
      .bolt-glow {{ fill: #ff5a1f; filter: url(#glow); opacity: .55;
                   animation: glowPulse 3.2s ease-in-out infinite;
                   transform-origin: {DISC_CX}px {DISC_CY}px; }}
      .warm {{ filter: url(#softblur); animation: warmPulse 4.2s ease-in-out infinite;
              transform-origin: {DISC_CX}px {DISC_CY}px; }}
      .shine {{ fill: url(#shine); mix-blend-mode: screen; opacity: 0;
               animation: shineSweep 4.5s linear infinite; }}
      .ember {{ fill: #ff7a3d; opacity: 0; animation: emberRise 6s linear infinite; }}
      @keyframes glowPulse {{ 0%,100% {{ opacity:.45; transform:scale(1); }} 50% {{ opacity:.8; transform:scale(1.015); }} }}
      @keyframes warmPulse {{ 0%,100% {{ opacity:.5; }} 50% {{ opacity:.85; }} }}
      @keyframes shineSweep {{
        0% {{ opacity:0; transform:translateY(-820px); }}
        12% {{ opacity:.9; }} 38% {{ opacity:.9; }}
        50%,100% {{ opacity:0; transform:translateY(820px); }}
      }}
      @keyframes emberRise {{
        0% {{ opacity:0; transform:translate(0,0) scale(1); }}
        12% {{ opacity:.95; }}
        100% {{ opacity:0; transform:translate(var(--dx,0px),-120px) scale(.4); }}
      }}
      @media (prefers-reduced-motion: reduce) {{
        .bolt-glow,.warm,.shine,.ember {{ animation:none !important; }}
        .bolt-glow {{ opacity:.55; }} .warm {{ opacity:.6; }} .ember {{ opacity:.35; }}
      }}
    </style>
  </defs>

  <circle cx="{DISC_CX}" cy="{DISC_CY}" r="{DISC_R}" fill="#000"/>
  <g clip-path="url(#discclip)">
    <circle cx="{DISC_CX}" cy="{DISC_CY}" r="{DISC_R}" fill="url(#bg)"/>
    <!-- cracked-stone texture -->
    <circle cx="{DISC_CX}" cy="{DISC_CY}" r="{DISC_R}" fill="#0b0b0b" filter="url(#grain)" opacity="0.5"/>
    <g>
{hairlines}
    </g>
    <!-- warm ambient glow bleeding from the fault -->
    <ellipse class="warm" cx="{(DISC_CX):.0f}" cy="{DISC_CY:.0f}" rx="200" ry="340"
             fill="url(#warmglow)" transform="rotate(38 {DISC_CX} {DISC_CY})"/>
    <!-- fissure branches -->
    <g>
{branches}
    </g>
    <!-- the fault: core + shine sweep, clipped to the disc -->
    <use href="#bolt" class="bolt-core"/>
    <g clip-path="url(#boltclip)">
      <rect class="shine" x="{DISC_CX - DISC_R:.0f}" y="{DISC_CY - DISC_R - 40:.0f}" width="{vs:.0f}" height="240"/>
    </g>
    <use href="#bolt" class="bolt-glow"/>
    <!-- embers -->
    <g>
{embers}    </g>
  </g>
</svg>
'''
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT} ({len(svg)} bytes, {len(EMBERS)} embers, "
          f"{hairlines.count('<path')} hairlines, {branches.count('<path')} branches)")


if __name__ == "__main__":
    main()
