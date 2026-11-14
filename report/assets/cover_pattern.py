# Generates report/assets/cover_bg.png. Run from report/assets: python3 cover_pattern.py
"""Cover background: rounded triangular tiles on a triangular grid, hatched channels between them,
seen in perspective (after the reference photo). Two tiles that share an edge are neon.
The text column is frosted (blurred and lightened). Deterministic."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
TW = 7200                                   # flat texture size (px)
a = 420.0; h = a * np.sqrt(3) / 2           # triangle side and height
inset, rc, sw = 24.0, 50.0, 5.0             # gap from the grid line, corner radius, outline width
PAPER, INK, NEON = 246, 18, (0xEA, 0xFF, 0x3D)
tex = Image.new("L", (TW, TW), PAPER); d = ImageDraw.Draw(tex)
for x in range(0, TW, 9): d.line([(x, 0), (x, TW)], fill=INK, width=3)          # one hatch direction, like an engraving
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
grid_lines(PAPER, 19)                       # a clear strip either side, so the line reads against the hatching
grid_lines(INK, 6)
def rounded(tri, grow):
    c = np.mean(tri, axis=0); ri = a / (2 * np.sqrt(3)); t = inset + rc
    inner = [c + (np.array(p) - c) * (ri - t) / ri for p in tri]
    pts = []
    for k in range(3):
        p = inner[k]; for_prev = inner[k - 1]; nxt = inner[(k + 1) % 3]
        for q2 in (for_prev, nxt):
            e = q2 - p; n = np.array([e[1], -e[0]]) / np.linalg.norm(e)
            if np.dot(n, p - c) < 0: n = -n
            pts.append(tuple(p + n * (rc + grow)))
    hull = sorted(pts, key=lambda p: np.arctan2(p[1] - c[1], p[0] - c[0]))
    return hull, inner
def draw_tile(dr, tri, fill):
    hull, inner = rounded(tri, sw)
    dr.polygon(hull, fill=INK)
    for p in inner: dr.ellipse([p[0] - rc - sw, p[1] - rc - sw, p[0] + rc + sw, p[1] + rc + sw], fill=INK)
    hull, inner = rounded(tri, 0)
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
NEON_TILES = {(best[0], best[1], 0), (best[0], best[1], 1)}           # an up and a down triangle that share an edge
neon_mask = Image.new("L", (TW, TW), 0); dn_ = ImageDraw.Draw(neon_mask)
for i, j, o, tri in tiles:
    if all(-a < p[0] < TW + a and -a < p[1] < TW + a for p in tri):
        draw_tile(d, tri, PAPER)
        if (i, j, o) in NEON_TILES: draw_tile(dn_, tri, 255)
out = tex.transform((W * Z, H * Z), Image.PERSPECTIVE, tuple(coef), Image.BICUBIC).resize((W * 2, H * 2), Image.LANCZOS)
nm = neon_mask.transform((W * Z, H * Z), Image.PERSPECTIVE, tuple(coef), Image.BICUBIC).resize((W * 2, H * 2), Image.LANCZOS)
g = np.asarray(out).astype(np.float32)
# depth haze: the far corner fades toward paper, as in the photo
yy, xx = np.mgrid[0:H * 2, 0:W * 2].astype(np.float32)
far = np.clip(1 - (xx / (W * 2) * 0.55 + yy / (H * 2) * 0.75), 0, 1) ** 1.6
g = g + (PAPER - g) * (0.85 * far)
rgb = np.repeat(g[..., None], 3, axis=2)
m = (np.asarray(nm).astype(np.float32) / 255)[..., None]
rgb = rgb * (1 - m) + np.array(NEON, float) * m
Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save("pattern.png")
# frosted text column
base = Image.open("pattern.png"); blur = np.asarray(base.filter(ImageFilter.GaussianBlur(34))).astype(np.float32)
frost = blur + (250 - blur) * 0.80
t = np.clip((xx / (W * 2) - 0.62) / 0.10, 0, 1); t = (t * t * (3 - 2 * t))[..., None]
final = np.asarray(base).astype(np.float32) * (1 - t) + frost * t
Image.fromarray(np.clip(final, 0, 255).astype(np.uint8)).save("cover_bg.png")
