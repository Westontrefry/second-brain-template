"""Generate the Azure constellation app icon master SVG from the locked tuner
settings, then a render harness Chrome can rasterize at any size.

Locked settings (from the tuner readout):
  hue #6aa5ff · sharpness 0.31 · glow 0.9 · spread 1.00 · dust 9
  · lead 4-point · lines blue · core on · layout dynamic
"""
import math
import os

OUT = os.path.dirname(os.path.abspath(__file__))

COLOR = "#6aa5ff"
SHARP = 0.31
SPREAD = 1.0
DUST_N = 9
BG = "#05060a"
CORE = "#f0f5ff"
EDGE_OP = 0.5


def star_path(cx, cy, r, points, inner):
    ri = r * inner
    n = points * 2
    d = ""
    for i in range(n):
        R = ri if i % 2 else r
        a = (math.pi / points) * i - math.pi / 2
        d += ("L" if i else "M") + f"{cx + R * math.cos(a):.3f},{cy + R * math.sin(a):.3f}"
    return d + "Z"


# Deterministic dust field — identical formula to the tuner's DUST[] array.
def dust_field():
    out = []
    for i in range(DUST_N):
        x = 9 + (i * 37) % 82 + (i * 13) % 7
        y = 9 + (i * 53) % 82 + (i * 17) % 6
        r = 0.3 + ((i * 7) % 6) / 10
        o = 0.12 + ((i * 11) % 28) / 100
        out.append((x, y, round(r, 2), round(o, 2)))
    return out


# --- geometry in the 100-unit design space (matches the tuner exactly) ---
large = 15.0
medR = large * (0.78 - 0.10 * SPREAD)   # 10.2
smR = large * (0.52 - 0.14 * SPREAD)    # 5.7
POS = [(36, 62), (60, 33), (71, 61)]    # dynamic layout: large, med, small
STARS = [
    (POS[0][0], POS[0][1], large, 4, "gB"),
    (POS[1][0], POS[1][1], medR, 4, "gS"),
    (POS[2][0], POS[2][1], smR, 4, "gS"),
]
PAIRS = [(0, 1), (1, 2), (2, 0)]

# --- superellipse squircle in the 1024 master space (Apple-like curvature) ---
CX = CY = 512.0
A = 412.0            # half-size -> 824px body, 100px margin each side
N_EXP = 5.0          # superellipse exponent; corner ~ macOS Big Sur squircle
EXP = 2.0 / N_EXP


def squircle_path(samples=240):
    pts = []
    for k in range(samples):
        t = 2 * math.pi * k / samples
        ct, st = math.cos(t), math.sin(t)
        x = CX + A * math.copysign(abs(ct) ** EXP, ct)
        y = CY + A * math.copysign(abs(st) ** EXP, st)
        pts.append(f"{x:.2f},{y:.2f}")
    return "M" + "L".join(pts) + "Z"


# design(4..96) -> body(100..924)
S = 824.0 / 92.0
T = 100.0 - 4.0 * S


def build_svg():
    sq = squircle_path()
    parts = []
    parts.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" width="1024" height="1024" role="img">')
    parts.append('<title>Second brain — constellation icon</title>')
    parts.append('<desc>Three connected blue four-point stars of three sizes forming a triangle on a deep-space squircle.</desc>')
    parts.append("<defs>")
    parts.append(f'<clipPath id="sq"><path d="{sq}"/></clipPath>')
    # self-coloured glow, baked as SVG filters (stdDeviation in design units,
    # so it scales cleanly at every raster size)
    parts.append('<filter id="gB" x="-60%" y="-60%" width="220%" height="220%">'
                 f'<feDropShadow dx="0" dy="0" stdDeviation="0.42" flood-color="{COLOR}" flood-opacity="1"/></filter>')
    parts.append('<filter id="gS" x="-60%" y="-60%" width="220%" height="220%">'
                 f'<feDropShadow dx="0" dy="0" stdDeviation="0.30" flood-color="{COLOR}" flood-opacity="1"/></filter>')
    parts.append("</defs>")
    parts.append('<g clip-path="url(#sq)">')
    parts.append(f'<g transform="translate({T:.3f},{T:.3f}) scale({S:.5f})">')
    parts.append(f'<rect x="4" y="4" width="92" height="92" fill="{BG}"/>')
    for (x, y, r, o) in dust_field():
        parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#cfd6ff" opacity="{o}"/>')
    for (i, j) in PAIRS:
        a, b = STARS[i], STARS[j]
        parts.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" '
                     f'stroke="{COLOR}" stroke-width="1.1" stroke-linecap="round" opacity="{EDGE_OP}"/>')
    for (x, y, r, pts, fid) in STARS:
        parts.append(f'<path d="{star_path(x, y, r, pts, SHARP)}" fill="{COLOR}" filter="url(#{fid})"/>')
    for (x, y, r, pts, fid) in STARS:
        parts.append(f'<circle cx="{x}" cy="{y}" r="{r * 0.16:.3f}" fill="{CORE}" opacity="0.95"/>')
    parts.append("</g></g>")
    # faint rim light on the squircle edge
    parts.append(f'<path d="{sq}" fill="none" stroke="rgba(255,255,255,0.09)" stroke-width="2"/>')
    parts.append("</svg>")
    return "".join(parts)


svg = build_svg()
with open(os.path.join(OUT, "icon-master.svg"), "w") as f:
    f.write(svg)

harness = (
    "<!doctype html><html><head><meta charset='utf-8'>"
    "<style>html,body{margin:0;padding:0;background:transparent}"
    "svg{display:block;width:100vw;height:100vh}</style></head><body>"
    + svg + "</body></html>"
)
with open(os.path.join(OUT, "render.html"), "w") as f:
    f.write(harness)

print("wrote icon-master.svg (%d bytes) and render.html" % len(svg))
