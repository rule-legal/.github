# /// script
# dependencies = ["skia-pathops", "fonttools", "pillow"]
# ///
"""A portrait glass codex: brown glass covers with gold edges, twelve stiff clear glass pages,
the first page leaning out on its spine hinge with a gold inscription that glows.

Geometry: u runs from the spine (left) across the page, v runs up, z runs into the book.
Oblique projection: screen = O + u·EX + (0, -v) + z·EZ.  A leaf hinged at the spine, opened by α
toward the viewer, maps (u, v) at depth z0 to (u·cos α, v, z0 - u·sin α).
"""
import json, math, os, sys
import pathops
from PIL import Image, ImageDraw, ImageFilter
root = sys.argv[1]
env = lambda k, d: float(os.environ.get(k, d))
W, H = env("W", 340), env("H", 470)
N, PT, PG, COV = 12, env("PT", 8), env("PG", 4), env("COV", 16)
DEPTH = N * (PT + PG)
EX, EZ = (1.0, 0.0), (env("EZX", 0.52), env("EZY", 0.30))
A_COVER, A_PAGE = math.radians(env("AC", 30)), math.radians(env("AP", 14))
U, I, D = pathops.PathOp.UNION, pathops.PathOp.INTERSECTION, pathops.PathOp.DIFFERENCE
op = pathops.op

def raw(u, v, z): return (u * EX[0] + z * EZ[0], -v + u * EX[1] + z * EZ[1])
bb = [raw(u, v, z) for u in (0, W + 10) for v in (-8, H + 8) for z in (0, DEPTH + 2 * COV)] + [raw(W * math.cos(A_COVER), v, -W * math.sin(A_COVER)) for v in (-8, H + 8)]
OX = 512 - (min(p[0] for p in bb) + max(p[0] for p in bb)) / 2 + env("DX", 0)
OY = 512 - (min(p[1] for p in bb) + max(p[1] for p in bb)) / 2 + env("DY", 0)
def P(u, v, z): x, y = raw(u, v, z); return (OX + x, OY + y)
def leaf(u, v, z0, a): return P(u * math.cos(a), v, z0 - u * math.sin(a))

def poly(pts):
    p = pathops.Path(); pen = p.getPen(); pen.moveTo(pts[0])
    for q in pts[1:]: pen.lineTo(q)
    pen.closePath(); return p
def hull(pts):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts)); cr = lambda o, a, b: (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo, hi = [], []
    for q in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], q) <= 0: lo.pop()
        lo.append(q)
    for q in reversed(pts):
        while len(hi) >= 2 and cr(hi[-2], hi[-1], q) <= 0: hi.pop()
        hi.append(q)
    return lo[:-1] + hi[:-1]
def rrect_uv(u0, v0, u1, v1, r, n=6):
    cu, cv, w, h = (u0+u1)/2, (v0+v1)/2, u1-u0, v1-v0; pts = []
    for (qx, qy, a0) in [(cu+w/2-r, cv+h/2-r, 0), (cu-w/2+r, cv+h/2-r, 90), (cu-w/2+r, cv-h/2+r, 180), (cu+w/2-r, cv-h/2+r, 270)]:
        for i in range(n+1):
            a = math.radians(a0 + 90*i/n); pts.append((qx + r*math.cos(a), qy + r*math.sin(a)))
    return pts
def slab(uv, z0, t, a=0.0):  # a rigid sheet of thickness t, hinged at the spine, opened by a
    return poly(hull([leaf(u, v, z0, a) for u, v in uv] + [leaf(u, v, z0 + t, a) for u, v in uv]))
def face(uv, z0, a=0.0): return poly([leaf(u, v, z0, a) for u, v in uv])
def svg_of(path):
    from fontTools.pens.svgPathPen import SVGPathPen
    pen = SVGPathPen(None); path.draw(pen)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024"><path fill="#000" fill-rule="nonzero" d="{pen.getCommands()}"/></svg>\n'

cover_uv = rrect_uv(0, -8, W + 10, H + 8, 16)
page_uv = rrect_uv(3, 0, W, H, 8)
zp = lambda i: COV + i * (PT + PG) + PG / 2          # page i, 0 = front
assets = {
    "back-cover.svg": slab(cover_uv, COV + DEPTH, COV),
    "front-cover.svg": slab(cover_uv, 0, COV, A_COVER),
    "front-face.svg": face(cover_uv, 0, A_COVER),
    "magic.svg": slab(page_uv, zp(0), PT, A_PAGE),
}
assets["cover-edge.svg"] = op(assets["front-cover.svg"], assets["front-face.svg"], D)
assets["back-edge.svg"] = op(assets["back-cover.svg"], face(cover_uv, COV + DEPTH), D)
fo, fi = rrect_uv(22, 16, W - 12, H - 16, 10), rrect_uv(30, 24, W - 20, H - 24, 6)
assets["frame.svg"] = op(face(fo, 0, A_COVER), face(fi, 0, A_COVER), D)
for i in range(1, N): assets[f"p{i:02d}.svg"] = slab(page_uv, zp(i), PT)

# the inscription: rows of script-like strokes on the magic page's face
rows = [(0.84, [(0.12, 0.30), (0.34, 0.52), (0.56, 0.86)]), (0.76, [(0.12, 0.44), (0.48, 0.66), (0.70, 0.90)]),
        (0.68, [(0.12, 0.24), (0.28, 0.62), (0.66, 0.84)]), (0.60, [(0.12, 0.40), (0.44, 0.58), (0.62, 0.90)]),
        (0.52, [(0.12, 0.34), (0.38, 0.72), (0.76, 0.86)]), (0.44, [(0.12, 0.28), (0.32, 0.50), (0.54, 0.90)]),
        (0.36, [(0.12, 0.46), (0.50, 0.64), (0.68, 0.80)]), (0.28, [(0.12, 0.32), (0.36, 0.60)])]
ins = None; sh = env("SH", 13)
for fv, strokes in rows:
    for a, b in strokes:
        r = face(rrect_uv(a * W, fv * H - sh / 2, b * W, fv * H + sh / 2, sh / 2), zp(0) - 0.5, A_PAGE)
        ins = r if ins is None else op(ins, r, U)
if os.environ.get("INK") == "binary":   # rows of real bits: "rule.law" in ASCII, repeated; 1 = rounded bar, 0 = rounded ring
    bits = "".join(f"{b:08b}" for b in b"rule.law" * 4)
    gh, gw0, gw1, st, sp, gsp = env("GH", 30), env("GW0", 19), env("SW", 7), env("ST", 6), env("SP", 7), env("GSP", 17)
    rows_v = [0.86 - k * env("RS", 0.078) for k in range(int(env("NR", 8)))]
    ins, k = None, 0
    for fv in rows_v:
        u = 0.10 * W; v0 = fv * H - gh / 2
        while True:
            b = bits[k % len(bits)]; w = gw0 if b == "0" else gw1
            if u + w > 0.92 * W: break
            if b == "1": g = face(rrect_uv(u, v0, u + w, v0 + gh, w / 2), zp(0) - 0.5, A_PAGE)
            else: g = op(face(rrect_uv(u, v0, u + w, v0 + gh, w / 2), zp(0) - 0.5, A_PAGE), face(rrect_uv(u + st, v0 + st, u + w - st, v0 + gh - st, (w - 2 * st) / 2), zp(0) - 0.5, A_PAGE), D)
            ins = g if ins is None else op(ins, g, U)
            k += 1; u += w + (gsp if k % 8 == 0 else sp)
        k += 3
assets["inscription.svg"] = op(ins, assets["front-cover.svg"], D)          # exposed: bright
assets["inscription-behind.svg"] = op(ins, assets["front-cover.svg"], I)   # seen through the cover: faint
assets["magic-edge.svg"] = op(assets["magic.svg"], face(page_uv, zp(0), A_PAGE), D)

def glow_png(path, rgb):
    """soft gold light centred on the exposed part of the magic page"""
    cu, cv = env("GU", 0.74) * W, 0.56 * H
    cx, cy = leaf(cu, cv, zp(0), A_PAGE)
    im = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rx, ry = env("GRX", 120), env("GRY", 210)
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(*rgb, 255))
    im.filter(ImageFilter.GaussianBlur(env("GB", 70))).save(path)

def c(r, g, b, a=1.0): return f"display-p3:{r:.5f},{g:.5f},{b:.5f},{a:.5f}"
def solid(rgb): return {"solid": c(*rgb)}
def lin(a, b, s=(0.2, 0.1), e=(0.9, 0.9)): return {"linear-gradient": [c(*a), c(*b)], "orientation": {"start": {"x": s[0], "y": s[1]}, "stop": {"x": e[0], "y": e[1]}}}
def layer(name, image, fill, dark=None, opacity=None, glass=True, blend=None):
    L_ = {"name": name, "image-name": image, "glass": glass, "fill-specializations": [{"value": fill}] + ([{"appearance": "dark", "value": dark}] if dark else [])}
    if opacity is not None: L_["opacity"] = opacity
    if blend: L_["blend-mode"] = blend
    return L_
def raster(name, image, opacity, blend="plus-lighter"):
    return {"name": name, "image-name": image, "glass": False, "opacity": opacity, "blend-mode": blend}
def photos_group(name, layers, translucency=0.2, refract=(0.23, 0.14), opacity=0.95, shadow_light=0.5, shadow_dark=0.4):
    return {"name": name, "layers": list(reversed(layers)), "lighting": "individual", "specular": True, "opacity": opacity,
            "blend-mode-specializations": [{"value": "multiply"}, {"appearance": "dark", "value": "hard-light"}, {"appearance": "tinted", "value": "plus-lighter"}],
            "refractivity": {"enabled": True, "strength": refract[0], "depth": refract[1]},
            "translucency-specializations": [{"value": {"enabled": True, "value": translucency}}, {"appearance": "tinted", "value": {"enabled": True, "value": 0.4}}],
            "shadow-specializations": [{"value": {"kind": "neutral", "opacity": shadow_light}}, {"appearance": "dark", "value": {"kind": "neutral", "opacity": shadow_dark}},
                                       {"appearance": "tinted", "value": {"kind": "layer-color", "opacity": 0.5}}],
            "specular-highlight-placement-specializations": [{"value": "inside"}, {"appearance": "tinted", "value": "outside"}]}
def light_group(name, layers, opacity=1.0):
    return {"name": name, "layers": list(reversed(layers)), "lighting": "individual", "specular": False, "opacity": opacity,
            "shadow": {"kind": "none", "opacity": 0}}

def codex(m):
    g = []   # back to front
    pa = env("PAGE_A", 0.55)   # at most four groups: the back cover and the eleven plain pages share one
    pages = [layer(f"page {i + 1}", f"p{i:02d}.svg", solid((*m["page"], pa)), solid((0.80, 0.84, 0.92, env("PAGE_AD", 0.8)))) for i in range(N - 1, 0, -1)]
    g.append(photos_group("Back cover and pages", [layer("back", "back-cover.svg", solid(m.get("back", m["cover"])), solid(m["cover_d"]), opacity=m.get("back_op")),
                                                   layer("gold edge", "back-edge.svg", solid(m["gold"]), solid(m["gold_d"]))] + pages,
                          translucency=0.3, opacity=1.0, shadow_light=0.3, shadow_dark=0.3))
    g.append(photos_group("Magic page", [layer("page", "magic.svg", solid(m["page"]), solid(m["page_d"])),
                                         layer("edge", "magic-edge.svg", solid(m["gold"]), solid(m["gold_d"]), opacity=0.7)],
                          translucency=0.35, opacity=1.0, shadow_light=0.35, shadow_dark=0.3))
    g.append(photos_group("Front cover", [layer("cover", "front-cover.svg", solid(m["cover"]), solid(m["cover_d"]), opacity=m["cover_op"]),
                                          layer("gold edge", "cover-edge.svg", solid(m["gold"]), solid(m["gold_d"])),
                                          layer("frame", "frame.svg", solid(m["gold"]), solid(m["gold_d"]), opacity=0.8, glass=False)],
                          translucency=m["cover_tr"], opacity=1.0, refract=(0.3, 0.35)))
    gl = raster("glow", "glow.png", m["glow_op"], blend="normal"); gl["opacity-specializations"] = [{"value": m["glow_op"]}, {"appearance": "dark", "value": m["glow_op"] * 0.55}]; del gl["opacity"]
    ink = lambda: (lin(m["ink_hi"], m["ink_lo"], (0.85, 0.2), (0.35, 0.9)), lin(m["ink_hi_d"], m["ink_lo"], (0.85, 0.2), (0.35, 0.9)))
    glow = light_group("Glow", [gl,
                                layer("inscription behind", "inscription-behind.svg", *ink(), glass=False, opacity=0.28),
                                layer("inscription", "inscription.svg", lin(m["ink_hi"], m["ink_lo"], (0.85, 0.2), (0.35, 0.9)), lin(m["ink_hi_d"], m["ink_lo"], (0.85, 0.2), (0.35, 0.9)), glass=False)])
    gl["blend-mode-specializations"] = [{"value": "normal"}, {"appearance": "dark", "value": "plus-lighter"}]; del gl["blend-mode"]
    g.append(glow)
    return {"fill-specializations": [{"value": "system-light"}, {"appearance": "dark", "value": "system-dark"}], "groups": list(reversed(g))}

BASE = dict(gold=(0.95, 0.74, 0.30), gold_d=(0.98, 0.80, 0.38), page=(0.97, 0.98, 0.99), page_d=(0.60, 0.62, 0.66),
            ink_hi=(0.93, 0.66, 0.14), ink_hi_d=(1.0, 0.84, 0.36), ink_lo=(0.95, 0.70, 0.25, 0.18), cover_op=0.88, cover_tr=0.45, glow_op=0.45)
concepts = {
    "V1-walnut": dict(BASE, cover=(0.74, 0.54, 0.34), cover_d=(0.46, 0.28, 0.14)),
    "V2-cognac": dict(BASE, cover=(0.86, 0.66, 0.42), cover_d=(0.58, 0.36, 0.18)),
    "rule-law": dict(BASE, cover=(0.74, 0.54, 0.34), cover_d=(0.46, 0.28, 0.14)),
    "rule-legal": dict(BASE, cover=(0.62, 0.64, 0.70), cover_d=(0.26, 0.28, 0.34), gold=(0.80, 0.82, 0.88), gold_d=(0.90, 0.92, 0.98),
                       ink_hi=(0.34, 0.38, 0.50), ink_hi_d=(0.94, 0.96, 1.0), ink_lo=(0.70, 0.74, 0.84, 0.18), glow_rgb=(200, 215, 255)),
    "V3-smoke":  dict(BASE, cover=(0.68, 0.56, 0.46), cover_d=(0.36, 0.25, 0.19), cover_tr=0.55, glow_op=0.55),
}
TAG = os.environ.get("TAG", "")
PALE = os.environ.get("PALE_BACK") == "1"
for name, m in [(k, v) for k, v in concepts.items() if k in os.environ.get("ONLY", k)]:
    if PALE: m = dict(m, back=(0.97, 0.94, 0.90), back_op=0.7)
    name = name + TAG
    d = os.path.join(root, name); os.makedirs(d, exist_ok=True)
    for a, p in assets.items(): open(f"{d}/{a}", "w").write(svg_of(p))
    glow_png(f"{d}/glow.png", m.get("glow_rgb", (255, 196, 80)))
    d_ = {"features": ["refractivity", "specular-location"], **codex(m), "supported-platforms": {"squares": "shared"}}
    json.dump(d_, open(f"{d}/icon.json", "w"), indent=2, sort_keys=True); print(name, len(d_["groups"]), "groups")
