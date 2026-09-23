# /// script
# dependencies = ["skia-pathops", "pillow", "fonttools"]
# ///
"""The section sign, geometry fixed; materials and grounds explored."""
import json, math, os, sys
import pathops

root = sys.argv[1]; only = sys.argv[2:]
C = 512
U, I, D = pathops.PathOp.UNION, pathops.PathOp.INTERSECTION, pathops.PathOp.DIFFERENCE
op = pathops.op
R, T = float(os.environ.get("R", 92)), float(os.environ.get("T", 58))

def poly(pts):
    p = pathops.Path(); pen = p.getPen(); pen.moveTo(pts[0])
    for q in pts[1:]: pen.lineTo(q)
    pen.closePath(); return p
def circle(r, cx=C, cy=C, n=120): return poly([(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)])
def arc_tube(cx, cy, r, t, a0, a1, n=72):
    A0, A1 = math.radians(a0), math.radians(a1)
    outer = [(cx + (r + t / 2) * math.cos(A0 + (A1 - A0) * i / n), cy + (r + t / 2) * math.sin(A0 + (A1 - A0) * i / n)) for i in range(n + 1)]
    inner = [(cx + (r - t / 2) * math.cos(A1 - (A1 - A0) * i / n), cy + (r - t / 2) * math.sin(A1 - (A1 - A0) * i / n)) for i in range(n + 1)]
    s = poly(outer + inner)
    for A in (A0, A1): s = op(s, circle(t / 2, cx + r * math.cos(A), cy + r * math.sin(A)), U)
    return s
def s_curve(cx, cy, r, t): return op(arc_tube(cx, cy - r, r, t, 0, -270), arc_tube(cx, cy + r, r, t, -90, 180), U)
def svg_of(path):
    from fontTools.pens.svgPathPen import SVGPathPen
    pen = SVGPathPen(None); path.draw(pen)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024"><path fill="#000" fill-rule="nonzero" d="{pen.getCommands()}"/></svg>\n'

s_up, s_down = s_curve(C, C - R, R, T), s_curve(C, C + R, R, T)
assets = {"s-up.svg": s_up, "s-down.svg": s_down, "section.svg": op(s_up, s_down, U), "ring.svg": op(s_up, s_down, I)}

def c(r, g, b, a=1.0): return f"display-p3:{r:.5f},{g:.5f},{b:.5f},{a:.5f}"
def grad(top, bottom, start=(0.5, 0), stop=(0.5, 1)):
    return {"linear-gradient": [top, bottom], "orientation": {"start": {"x": start[0], "y": start[1]}, "stop": {"x": stop[0], "y": stop[1]}}}
def spec(light, dark=None):
    s_ = [{"value": light}]
    if dark is not None: s_.append({"appearance": "dark", "value": dark})
    return s_
def layer(name, image, fill=None, dark=None, glass=True, opacity=None, blend=None):
    L = {"name": name, "image-name": image, "glass": glass}
    if fill is not None: L["fill-specializations"] = spec(fill, dark)
    if opacity is not None: L["opacity"] = opacity
    if blend: L["blend-mode"] = blend
    return L
def group(name, layers, shadow=("neutral", 0.5), translucency=None, refract=None, blur=None, specular=True, placement=None, blend=None, opacity=None, blend_spec=None):
    G = {"name": name, "layers": layers, "lighting": "individual", "specular": specular, "shadow": {"kind": shadow[0], "opacity": shadow[1]}}
    if translucency is not None: G["translucency"] = {"enabled": True, "value": translucency}
    if refract: G["refractivity"] = {"enabled": True, "strength": refract[0], "depth": refract[1]}
    if blur is not None: G["blur-material"] = blur
    if placement: G["specular-highlight-placement"] = placement
    if blend: G["blend-mode"] = blend
    if blend_spec: G["blend-mode-specializations"] = blend_spec
    if opacity is not None: G["opacity"] = opacity
    return G
WHITE = c(1, 1, 1)

# grounds
INK = spec(grad(c(.13, .12, .22), c(.06, .05, .12)), grad(c(.08, .07, .15), c(.02, .02, .06)))
LIGHT = spec("system-light", "system-dark")
BLUE = spec(grad(c(.22, .50, 1.0), c(.10, .16, .70)), grad(c(.14, .30, .75), c(.05, .07, .38)))
BORDEAUX = spec(grad(c(.62, .12, .24), c(.32, .04, .12)), grad(c(.42, .07, .16), c(.18, .02, .07)))
VIOLET = spec(grad(c(.42, .28, .95), c(.20, .09, .58)), grad(c(.28, .16, .66), c(.10, .04, .36)))
SLATE = spec(grad(c(.30, .32, .42), c(.16, .17, .25)), grad(c(.20, .21, .29), c(.08, .08, .13)))
GREEN = spec(grad(c(.10, .45, .32), c(.03, .20, .15)), grad(c(.06, .30, .22), c(.02, .12, .09)))

# materials: (upper fill, lower fill, translucency, refraction, shadow kind, extra)
GOLD = (grad(c(1.00, 0.90, 0.55), c(0.92, 0.64, 0.16)), grad(c(1.00, 0.82, 0.40), c(0.84, 0.50, 0.08)), 0.25, (0.35, 0.45), "layer-color")
FROST = (grad(WHITE, c(.90, .94, 1)), grad(WHITE, c(.86, .91, 1)), 0.35, (0.3, 0.4), "neutral")
SILVER = (grad(c(.97, .98, 1), c(.58, .63, .78)), grad(c(.92, .94, 1), c(.50, .55, .72)), 0.25, (0.35, 0.45), "layer-color")
CLEAR = ({"solid": c(1, 1, 1, .28)}, {"solid": c(1, 1, 1, .22)}, 0.7, (0.9, 0.6), "neutral")
DUO = (grad(c(.30, .62, 1), c(.20, .45, 1)), grad(c(1, .40, .55), c(.85, .30, .75)), 0.25, (0.35, 0.45), "neutral")

def section(ground, mat, blend_spec=None, opacity=None, blur=None):
    up, down, tr, rf, sk = mat
    groups = [group("S upper", [layer("s", "s-up.svg", up, opacity=opacity)], shadow=(sk, 0.5), translucency=tr, refract=rf, blur=blur, placement="inside", blend_spec=blend_spec),
              group("S lower", [layer("s", "s-down.svg", down, opacity=opacity)], shadow=(sk, 0.5), translucency=tr, refract=rf, blur=blur, placement="inside", blend_spec=blend_spec),
              group("Specular", [layer("cap", "section.svg", {"solid": WHITE}, opacity=0)], shadow=("neutral", 0.5), placement="inside")]
    return {"fill-specializations": ground, "groups": list(reversed(groups))}

PHOTOS_BLEND = [{"value": "multiply"}, {"appearance": "dark", "value": "hard-light"}]
concepts = {
    "K1-gold-ink": section(INK, GOLD),
    "K2-gold-light": section(LIGHT, GOLD),
    "K3-frost-blue": section(BLUE, FROST),
    "K4-frost-bordeaux": section(BORDEAUX, FROST),
    "K5-clear-blue": section(BLUE, CLEAR),
    "K6-duo-light": section(LIGHT, DUO, blend_spec=PHOTOS_BLEND, opacity=0.95),
    "K7-silver-slate": section(SLATE, SILVER),
    "K8-gold-green": section(GREEN, GOLD),
    "K9-gold-bordeaux": section(BORDEAUX, GOLD),
    "K10-frost-violet": section(VIOLET, FROST),
}
for name, d_ in concepts.items():
    if only and name not in only: continue
    d = os.path.join(root, name); os.makedirs(d, exist_ok=True)
    used = {l["image-name"] for g in d_["groups"] for l in g["layers"]}
    for a, p in assets.items():
        if a in used: open(f"{d}/{a}", "w").write(svg_of(p))
    d_ = {"features": ["refractivity", "specular-location"], **d_, "supported-platforms": {"squares": "shared"}}
    json.dump(d_, open(f"{d}/icon.json", "w"), indent=2, sort_keys=True)
    print(name)

# --- the pair: gold for rule.law, silver for rule.legal, on the system grounds ---------------------------------
if os.environ.get("PAIR"):
    concepts = {"rule-law": section(LIGHT, GOLD), "rule-legal": section(LIGHT, SILVER)}
    for name, d_ in concepts.items():
        d = os.path.join(root, name); os.makedirs(d, exist_ok=True)
        for a, p in assets.items(): open(f"{d}/{a}", "w").write(svg_of(p))
        d_ = {"features": ["refractivity", "specular-location"], **d_, "supported-platforms": {"squares": "shared"}}
        json.dump(d_, open(f"{d}/icon.json", "w"), indent=2, sort_keys=True)
        print(name)
