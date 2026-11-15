# Generates report/assets/cover_bg.png. Run from report/assets: python3 cover_pattern.py
"""Cover background: rounded triangular tiles on a triangular grid, hatched channels between them,
seen in perspective (after the reference photo). Two tiles that share an edge are neon.
The text column is frosted (blurred and lightened). Deterministic."""
import numpy as np, sys
STYLE = sys.argv[1] if len(sys.argv) > 1 else "ink"   # "ink" or "pencil"
from PIL import Image, ImageDraw, ImageFilter
TW = 7200                                   # flat texture size (px)
a = 420.0; h = a * np.sqrt(3) / 2           # triangle side and height
inset, rc, sw = 24.0, 50.0, 5.0             # gap from the grid line, corner radius, outline width
PAPER, INK, NEON = 246, 18, (0xEA, 0xFF, 0x3D)
tex = Image.new("L", (TW, TW), PAPER); d = ImageDraw.Draw(tex)
_hr = np.random.default_rng(5)
for x in range(0, TW, 9):                                                    # one hatch direction, like an engraving
    if STYLE == "ink":
        d.line([(x, 0), (x, TW)], fill=INK, width=3)
    else:                                                                     # pencil, ruled: straight, but pressure and spacing vary a little
        xx_ = x + _hr.normal(0, 1.1); v = int(_hr.uniform(INK, 95)); wd = int(_hr.choice([2, 3, 3]))
        y = 0
        while y < TW:
            L = _hr.uniform(1500, 6000) if _hr.random() < 0.85 else _hr.uniform(200, 900)
            d.line([(xx_, y), (xx_ + _hr.normal(0, 0.4), y + L)], fill=v, width=wd)
            y += L + (_hr.uniform(6, 40) if _hr.random() < 0.5 else 0)
tiles = []
for j in range(-1, int(TW / h) + 2):
    for i in range(-2, int(TW / a) + 3):
        x0 = i * a + ((j + 1) % 2) * a / 2; y0 = j * h        # rows aligned with the grid-line vertices
        up = [(x0, y0 + h), (x0 + a, y0 + h), (x0 + a / 2, y0)]
        dn = [(x0 + a / 2, y0), (x0 + 3 * a / 2, y0), (x0 + a, y0 + h)]
        tiles += [(i, j, 0, up), (i, j, 1, dn)]
def grid_lines(color, width):                                                # the three families of grid lines
    for k in range(-2 * int(TW / h), int(3 * TW / h) + 2):
        y = k * h; d.line([(0, y), (TW, y)], fill=color, width=width)
        for sgn in (1, -1):
            x = k * a; d.line([(x, 0), (x + sgn * TW / np.sqrt(3), TW)], fill=color, width=width)
grid_lines(PAPER, 13)                       # a clear strip either side, so the line reads against the hatching
grid_lines(INK, 6)
if STYLE == "pencil":                                                        # light guide lines left from the construction
    _cr = np.random.default_rng(12)
    for _ in range(26):
        k = _cr.uniform(-TW / h, 2 * TW / h); fam = _cr.integers(3); off = _cr.uniform(0.2, 0.8)
        if fam == 0: y = (k + off) * h; d.line([(0, y), (TW, y)], fill=212, width=2)
        else:
            x = (k + off) * a; sg = 1 if fam == 1 else -1; d.line([(x, 0), (x + sg * TW / np.sqrt(3), TW)], fill=212, width=2)
rng = np.random.default_rng(15)
INSETS = np.array([3.0, 7.0, 14.0, 30.0]); PROB = [0.38, 0.27, 0.23, 0.12]   # on the line, close, narrow channel, the occasional wide one
RADII = np.array([22.0, 40.0, 62.0]); RPROB = [0.3, 0.45, 0.25]                # some corners nearly sharp, some very round
def rounded(tri, grow, ins, rc):
    """Rounded triangle inside tri, each edge pulled in by its own inset (ins[k] for edge k -> k+1)."""
    c = np.mean(tri, axis=0); P = [np.array(p, float) for p in tri]; lines = []
    for k in range(3):
        p, q2 = P[k], P[(k + 1) % 3]; e = q2 - p; n = np.array([e[1], -e[0]]) / np.linalg.norm(e)
        if np.dot(n, c - p) < 0: n = -n
        lines.append((p + n * (ins[k] + rc), e))
    inner = []
    for k in range(3):                                          # vertex k sits between edges k-1 and k
        (p1, e1), (p2, e2) = lines[k - 1], lines[k]
        A_ = np.array([e1, -e2]).T; t_ = np.linalg.solve(A_, p2 - p1); inner.append(p1 + e1 * t_[0])
    cc = np.mean(inner, axis=0); pts = []
    for k in range(3):
        p = inner[k]
        for q2 in (inner[k - 1], inner[(k + 1) % 3]):
            e = q2 - p; n = np.array([e[1], -e[0]]) / np.linalg.norm(e)
            if np.dot(n, p - cc) < 0: n = -n
            pts.append(tuple(p + n * (rc + grow)))
    hull = sorted(pts, key=lambda p: np.arctan2(p[1] - cc[1], p[0] - cc[0]))
    return hull, inner
def draw_tile(dr, tri, fill, ins, rc, ink=None):
    ink = INK if ink is None else ink
    hull, inner = rounded(tri, sw, ins, rc)
    dr.polygon(hull, fill=ink)
    for p in inner: dr.ellipse([p[0] - rc - sw, p[1] - rc - sw, p[0] + rc + sw, p[1] + rc + sw], fill=ink)
    hull, inner = rounded(tri, 0, ins, rc)
    dr.polygon(hull, fill=fill)
    for p in inner: dr.ellipse([p[0] - rc, p[1] - rc, p[0] + rc, p[1] + rc], fill=fill)
# perspective: output corners map to a quad on the flat texture (near bottom right, far top left)
W, H, Z = 1600, 900, 3
src = np.array([[0, 0], [W * Z, 0], [W * Z, H * Z], [0, H * Z]], float)
dst = np.array([[300, 500], [6300, 1900], [4600, 4600], [2000, 4900]], float)
A = []
for (x, y), (X, Y) in zip(src, dst):
    A += [[x, y, 1, 0, 0, 0, -X * x, -X * y], [0, 0, 0, x, y, 1, -Y * x, -Y * y]]
coef = np.linalg.solve(np.array(A), dst.reshape(-1))
def to_tex(x, y):
    den = coef[6] * x + coef[7] * y + 1
    return ((coef[0] * x + coef[1] * y + coef[2]) / den, (coef[3] * x + coef[4] * y + coef[5]) / den)
TX, TY = to_tex(560 * Z, 590 * Z)                                     # target on the cover: left third, lower third
best = min(((np.hypot(*(np.mean(tri, axis=0) - [TX, TY])), (i, j, o)) for i, j, o, tri in tiles if o == 0))[1]
apex = next(tri for i, j, o, tri in tiles if (i, j, o) == best)[2]            # the up tile's top vertex
above = min(((np.hypot(*(np.array(tri[2]) - apex)), (i, j, o)) for i, j, o, tri in tiles if o == 1))[1]
NEON_TILES = {best, above}                                                    # two tiles that meet at one point
neon_mask = Image.new("L", (TW, TW), 0); dn_ = ImageDraw.Draw(neon_mask)
for i, j, o, tri in tiles:
    if all(-a < p[0] < TW + a and -a < p[1] < TW + a for p in tri):
        ins = rng.choice(INSETS, 3, p=PROB); rcv = rng.choice(RADII, p=RPROB)
        if STYLE == "pencil" and rng.random() < 0.16:                        # traced twice, the second pass a hair off
            off = rng.normal(0, 2.2, 2); draw_tile(d, [(p[0] + off[0], p[1] + off[1]) for p in tri], PAPER, ins, rcv, ink=int(rng.uniform(70, 140)))
        draw_tile(d, tri, PAPER, ins, rcv)
        if (i, j, o) in NEON_TILES: draw_tile(dn_, tri, 255, ins, rcv)
if STYLE == "pencil":                                                          # a hand's wobble: smooth displacement of the flat drawing
    import cv2
    wr = np.random.default_rng(9)
    def field(cells, amp):
        f = wr.normal(0, 1, (cells, cells)).astype(np.float32)
        return cv2.resize(f, (TW, TW), interpolation=cv2.INTER_CUBIC) * amp
    dx = field(48, 0.0); dy = field(48, 0.0)
    gx, gy = np.meshgrid(np.arange(TW, dtype=np.float32), np.arange(TW, dtype=np.float32))
    tex = Image.fromarray(cv2.remap(np.asarray(tex), gx + dx, gy + dy, cv2.INTER_LINEAR, borderValue=PAPER))
    dxn = field(30, 3.0); dyn = field(30, 3.0)                                # the highlighter is looser than the pencil
    neon_mask = Image.fromarray(cv2.remap(np.asarray(neon_mask), gx + dxn, gy + dyn, cv2.INTER_LINEAR, borderValue=0))
    del gx, gy, dx, dy, dxn, dyn
out = tex.transform((W * Z, H * Z), Image.PERSPECTIVE, tuple(coef), Image.BICUBIC).resize((W * 2, H * 2), Image.LANCZOS)
nm = neon_mask.transform((W * Z, H * Z), Image.PERSPECTIVE, tuple(coef), Image.BICUBIC).resize((W * 2, H * 2), Image.LANCZOS)
g = np.asarray(out).astype(np.float32)
# depth haze: the far corner fades toward paper, as in the photo
yy, xx = np.mgrid[0:H * 2, 0:W * 2].astype(np.float32)
far = np.clip(1 - (xx / (W * 2) * 0.55 + yy / (H * 2) * 0.75), 0, 1) ** 1.6
g = g + (PAPER - g) * (0.85 * far)
m = (np.asarray(nm).astype(np.float32) / 255)[..., None]
if STYLE == "ink":
    rgb = np.repeat(g[..., None], 3, axis=2)
    rgb = rgb * (1 - m) + np.array(NEON, float) * m
else:                                                                         # graphite on paper, highlighter on top
    pr = np.random.default_rng(21); Hh, Ww = g.shape
    dark = np.clip((PAPER - g) / (PAPER - INK), 0, 1)
    grain = Image.fromarray(np.clip(pr.normal(128, 60, (Hh, Ww)), 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))
    grain = np.asarray(grain).astype(np.float32) / 255
    dark = np.clip(dark * 1.2, 0, 1) * (0.8 + 0.2 * np.clip(grain * 1.4 - 0.2, 0, 1)) * 0.88   # graphite: never black, a little paper tooth
    yy2, xx2 = np.mgrid[0:Hh, 0:Ww].astype(np.float32)
    for _ in range(4):                                                       # eraser marks: lines faded where something was rubbed out
        cx, cy = pr.uniform(0.05, 0.6) * Ww, pr.uniform(0.15, 0.95) * Hh; rx, ry = pr.uniform(40, 110), pr.uniform(18, 40); th = pr.uniform(0, np.pi)
        X_ = (xx2 - cx) * np.cos(th) + (yy2 - cy) * np.sin(th); Y_ = -(xx2 - cx) * np.sin(th) + (yy2 - cy) * np.cos(th)
        dark *= 1 - 0.45 * np.exp(-(X_ / rx) ** 2 - (Y_ / ry) ** 2)
    smudge = np.zeros_like(dark)
    for _ in range(5):                                                       # graphite smudges from the side of a hand
        cx, cy = pr.uniform(0.05, 0.62) * Ww, pr.uniform(0.1, 0.95) * Hh; rx, ry = pr.uniform(80, 220), pr.uniform(25, 60); th = pr.uniform(-0.6, 0.6)
        X_ = (xx2 - cx) * np.cos(th) + (yy2 - cy) * np.sin(th); Y_ = -(xx2 - cx) * np.sin(th) + (yy2 - cy) * np.cos(th)
        smudge += 0.06 * np.exp(-(X_ / rx) ** 2 - (Y_ / ry) ** 2)
    dark = np.clip(dark + smudge * (0.6 + 0.4 * grain), 0, 1)
    del yy2, xx2
    mott = np.asarray(Image.fromarray(np.clip(pr.normal(128, 40, (Hh // 40, Ww // 40)), 0, 255).astype(np.uint8)).resize((Ww, Hh), Image.BICUBIC)).astype(np.float32) / 255
    paper = np.array([241, 238, 231], float)[None, None, :] * (0.985 + 0.03 * mott[..., None]) + pr.normal(0, 1.6, (Hh, Ww, 1))
    graphite = np.array([62, 62, 66], float)
    rgb = paper * (1 - dark[..., None]) + graphite * dark[..., None]
    streak = np.asarray(Image.fromarray(np.clip(pr.normal(128, 50, (Hh, Ww // 6)), 0, 255).astype(np.uint8)).resize((Ww, Hh), Image.BICUBIC)).astype(np.float32) / 255
    hm = m * (0.78 + 0.22 * streak[..., None])                              # marker strokes leave uneven ink
    rgb = rgb * (1 - hm) + rgb * (np.array(NEON, float) / 255) * hm * 1.02 + np.array(NEON, float) * hm * 0.0
    rgb = np.where(hm > 0, rgb * (1 - 0.35 * hm) + np.array(NEON, float) * 0.35 * hm, rgb)
Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(f"pattern_{STYLE}.png")
# frosted text column: blur and lightening both grow smoothly from left to right
base = Image.open(f"pattern_{STYLE}.png"); B0 = np.asarray(base).astype(np.float32)
levels = [B0] + [np.asarray(base.filter(ImageFilter.GaussianBlur(rad))).astype(np.float32) for rad in (6, 14, 26, 40)]
u = np.clip((xx / (W * 2) - 0.46) / (0.74 - 0.46), 0, 1); u = u ** 3 * (u * (u * 6 - 15) + 10)   # smootherstep
pos = u * (len(levels) - 1); k0 = np.floor(pos).astype(int); fr = (pos - k0)[..., None]
k1 = np.minimum(k0 + 1, len(levels) - 1)
stack = np.stack(levels)                                          # (L, H, W, 3)
hh, ww = np.indices(k0.shape)
blurred = stack[k0, hh, ww] * (1 - fr) + stack[k1, hh, ww] * fr
FROST = 250 if STYLE == "ink" else np.array([243, 240, 234], float)
final = blurred + (FROST - blurred) * (0.82 * u ** 0.55)[..., None]   # lightening runs ahead of the blur, so the middle of the fade stays light
Image.fromarray(np.clip(final, 0, 255).astype(np.uint8)).save("cover_bg.png" if STYLE == "ink" else "cover_pencil_bg.png")
