# Generates report/assets/cover_bg.png. Run from report/assets: python3 cover_pattern.py
"""Cover background. The reference glyph is rebuilt on its own construction lattice (balls on circle
centres, hairline stems in the gaps, fillets carved by empty circles, tapered cones) and used as a
module. Neighbouring modules meet ball to ball, so the figure continues into a pattern.
One module's two directly joined nodes are neon. Deterministic."""
import numpy as np, random
from PIL import Image, ImageDraw, ImageFilter
random.seed(3); rng = np.random.default_rng(3)
S = 4; W1, H1 = 1600, 900
r = 11.0; s = 2 * r; w = 0.09 * r          # proportions of the reference: stem width about a twelfth of a ball
OX, OY = 14.0, 10.0                        # lattice origin (layout units)
PANEL_X = 1080                             # text panel starts here: grid only
PAPER, INK, NEON = (222, 219, 215), (44, 44, 42), (0xEA, 0xFF, 0x3D)
def P(x, y): return (OX + x * s, OY + y * s)          # lattice coords to layout units (.5 = gap line)
def q(p): return (p[0] * S, p[1] * S)

class Layer:
    def __init__(self):
        self.carve = Image.new("L", (W1*S, H1*S)); self.dc = ImageDraw.Draw(self.carve)    # shapes that the empty circles cut
        self.solid = Image.new("L", (W1*S, H1*S)); self.ds = ImageDraw.Draw(self.solid)    # balls and cones, never cut
    def ball(self, c): x, y = P(*c); self.ds.ellipse([(x-r)*S, (y-r)*S, (x+r)*S, (y+r)*S], fill=255)
    def rect(self, a, b):
        (x0, y0), (x1, y1) = P(*a), P(*b)
        self.dc.rectangle([min(x0,x1)*S, min(y0,y1)*S, max(x0,x1)*S, max(y0,y1)*S], fill=255)
    def stem(self, a, b):
        (x0, y0), (x1, y1) = P(*a), P(*b)
        if abs(x0 - x1) < 1e-6: box = [x0-w, min(y0,y1), x0+w, max(y0,y1)]
        else: box = [min(x0,x1), y0-w, max(x0,x1), y0+w]
        self.dc.rectangle([v*S for v in box], fill=255)
    def hull(self, a, ra, b, rb):
        (ax, ay), (bx, by) = P(*a), P(*b); dx, dy = bx-ax, by-ay; L = np.hypot(dx, dy); ux, uy = dx/L, dy/L
        k = (ra - rb) / L; h = np.sqrt(max(0, 1 - k*k)); pts = []
        for sg in (1, -1):
            nx, ny = ux*k - sg*uy*h, uy*k + sg*ux*h
            pts += [(ax+nx*ra, ay+ny*ra), (bx+nx*rb, by+ny*rb)]
        self.ds.polygon([q(pts[0]), q(pts[1]), q(pts[3]), q(pts[2])], fill=255)
        for c, rr in (((ax, ay), ra), ((bx, by), rb)): self.ds.ellipse([(c[0]-rr)*S, (c[1]-rr)*S, (c[0]+rr)*S, (c[1]+rr)*S], fill=255)

def motif(L, ax, ay, fx, fy, neon=None, skip=()):
    """The reference figure, anchored at lattice (ax, ay); fx, fy = +-1 mirror.
    Parts: ball A on top with a stem down its left edge, a bar on the bottom tangents of balls B and D,
    ball F under the bar joined to B by a thick diagonal, a cone down to ball E."""
    T = lambda x, y: (ax + fx * x, ay + (y if fy > 0 else 7 - y))      # a flipped figure keeps the same eight rows
    def tgt(name): return neon if (neon is not None and name in ("B", "F", "BF")) else L
    if "A" not in skip: L.ball(T(0, 0))
    tgt("B").ball(T(-2, 3)); L.ball(T(2, 3)); tgt("F").ball(T(-1, 4)); L.ball(T(0, 7))
    L.stem(T(-0.5, 0), T(-0.5, 3.5)); L.rect(T(-0.5, 0), T(0, 1))                 # stem and neck under A
    L.stem(T(-2, 3.5), T(2, 3.5))                                                 # the bar
    L.rect(T(-2, 3), T(-1, 3.5)); L.rect(T(1, 3), T(2, 3.5))                      # necks on B and D
    L.rect(T(-1, 3), T(0, 3.5))                                                   # junction fillets
    L.rect(T(0.5, 3.5), T(1, 4)); L.rect(T(0, 3.5), T(0.5, 4))
    tgt("BF").hull(T(-2, 3), r, T(-1, 4), r)                                      # B joined to F
    L.hull(T(0.5, 3.5), 1.6 * w, T(0, 7), r)                                      # the cone to E
    return [T(-2, 3), T(2, 3), T(-1, 4), T(0, 7), T(0, 0)]

ink, neon = Layer(), Layer()
balls = []
NEON_AT = (5, 3)                            # which module carries the neon pair (column, row in the tiling)
cols_t = int((PANEL_X - OX) / (5 * s)) ; rows_t = int(H1 / (8 * s)) + 2
for ci in range(-1, cols_t + 1):
    for ri in range(-1, rows_t):
        ax = 2 + ci * 5; ay = ri * 8 + (4 if ci % 2 else 0)                    # brick stagger by half a module
        if P(ax + 2.6, 0)[0] > PANEL_X - s: continue                            # keep a clean edge before the panel
        fx = random.choice((1, -1)); fy = random.choice((1, -1))
        is_neon = (ci, ri) == NEON_AT
        balls += motif(ink, ax, ay, fx, fy, neon=neon if is_neon else None)
# empty circles carve every lattice centre that is not a ball
bset = {(round(b[0]*2)/2, round(b[1]*2)/2) for b in balls}
empty = Image.new("L", (W1*S, H1*S)); de = ImageDraw.Draw(empty)
nx, ny = int(W1 / s) + 3, int(H1 / s) + 3
for i in range(-2, nx):
    for j in range(-2, ny):
        if (i, j) in bset: continue
        x, y = P(i, j); de.ellipse([(x-(r-w))*S, (y-(r-w))*S, (x+(r-w))*S, (y+(r-w))*S], fill=255)
E = np.asarray(empty).astype(np.float32) / 255
def flat(L):
    a = np.asarray(L.carve).astype(np.float32) * (1 - E)
    a = np.maximum(a, np.asarray(L.solid).astype(np.float32))
    return Image.fromarray(a.astype(np.uint8)).resize((W1*2, H1*2), Image.LANCZOS)
mi, mn = flat(ink), flat(neon)
mi_np = np.asarray(mi).astype(np.float32); mn_np = np.asarray(mn).astype(np.float32)
mi_np = np.clip(mi_np - mn_np, 0, 255)       # neon shapes replace ink where they overlap
# construction drawing at 2x
Z = 2; img = Image.new("RGB", (W1*Z, H1*Z), PAPER); d = ImageDraw.Draw(img)
for k in range(-12, int(W1 / (s/4)) + 12):
    x = (OX + k * s / 4) * Z; d.line([(x, 0), (x, H1*Z)], fill=(215, 211, 206))
for k in range(-12, int(H1 / (s/4)) + 12):
    y = (OY + k * s / 4) * Z; d.line([(0, y), (W1*Z, y)], fill=(215, 211, 206))
for i in range(-2, nx, 2):
    x = P(i, 0)[0] * Z; d.line([(x, 0), (x, H1*Z)], fill=(206, 189, 185))
for j in range(-2, ny, 2):
    y = P(0, j)[1] * Z; d.line([(0, y), (W1*Z, y)], fill=(206, 189, 185))
for i in range(-2, nx):                     # construction circles only where they shape a figure
    for j in range(-2, ny):
        x, y = P(i, j)
        if x > PANEL_X - s * 0.5: continue
        X, Y = int(x*Z), int(y*Z); R = int(s*Z*0.9)
        win = mi_np[max(0, Y-R):Y+R, max(0, X-R):X+R]
        if win.size and win.max() > 0 and (i, j) not in bset:
            d.ellipse([(x-r)*Z, (y-r)*Z, (x+r)*Z, (y+r)*Z], outline=(178, 174, 168))
for _ in range(70):
    a, b = random.sample(balls, 2); A, B_ = P(*a), P(*b)
    if np.hypot(A[0]-B_[0], A[1]-B_[1]) < 7 * s and max(A[0], B_[0]) < PANEL_X - s:
        d.line([(A[0]*Z, A[1]*Z), (B_[0]*Z, B_[1]*Z)], fill=(192, 188, 182))
arr = np.asarray(img).astype(np.float32) + rng.normal(0, 2.0, (H1*Z, W1*Z))[..., None]
m = (mi_np / 255)[..., None]; arr = arr * (1 - m) + np.array(INK, float) * m
mN = (mn_np / 255)[..., None]; arr = arr * (1 - mN) + np.array(NEON, float) * mN
edge = np.asarray(mn.filter(ImageFilter.MaxFilter(3))).astype(np.float32) - mn_np
e = np.clip(edge / 255, 0, 1)[..., None]; arr = arr * (1 - e) + np.array(INK, float) * e
Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save("cover_bg.png")
