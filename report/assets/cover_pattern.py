# Generates report/assets/cover_bg.png. Run from report/assets: python3 cover_pattern.py
"""Cover background: a sparse lattice of particle starbursts after the reference pattern,
full bleed at 3200x1800, one neon node. Deterministic (fixed seed)."""
import numpy as np
from PIL import Image, ImageFilter
rng = np.random.default_rng(7)
W, H = 3200, 1800
acc = np.zeros((H, W), np.float32); neon = np.zeros((H, W), np.float32)
base = np.deg2rad(np.array([92, 212, 332]))
def splat(buf, xs, ys, wts):
    m = (xs >= 0) & (xs < W - 1) & (ys >= 0) & (ys < H - 1)
    np.add.at(buf, (ys[m].astype(int), xs[m].astype(int)), wts[m].astype(np.float32))
def ray(buf, x0, y0, ang, length, n, bright):
    d = rng.exponential(length * 0.33, n); d = d[d < length]          # dense at the node, thinning fast
    n = d.size
    w = 0.6 + d * 0.006 + rng.exponential(0.6, n) * (d / length) * 6  # tight core, scattered dust further out
    off = rng.normal(0, 1, n) * w
    xs = x0 + np.cos(ang) * d - np.sin(ang) * off
    ys = y0 - np.sin(ang) * d - np.cos(ang) * off
    splat(buf, xs, ys, bright * np.exp(-d / (length * 0.45)) * rng.uniform(0.5, 1.5, n))
def faint_line(buf, x0, y0, ang, n, bright):
    d = rng.uniform(-3000, 3000, n); off = rng.normal(0, 0.9, n)
    xs = x0 + np.cos(ang) * d - np.sin(ang) * off; ys = y0 - np.sin(ang) * d - np.cos(ang) * off
    splat(buf, xs, ys, np.full(n, bright) * rng.uniform(0.2, 1.0, n))
nodes = []
a1, a2 = np.array([620.0, 0.0]), np.array([310.0, 440.0])
for i in range(-3, 8):
    for j in range(-2, 6):
        p = np.array([-120.0, -60.0]) + i * a1 + j * a2 + rng.normal(0, 60, 2)
        if -300 < p[0] < W + 300 and -300 < p[1] < H + 300:
            nodes.append(p)
NEON = np.array([1050.0, 1195.0])
for p in nodes:
    if np.hypot(*(p - NEON)) < 260: continue
    depth = rng.uniform(0.25, 1.0) ** 1.6                              # a few near and bright, most far and dim
    rot = rng.normal(0, 0.06)
    for ang in base:
        for sgn in (1, -1):
            if rng.random() < 0.25: continue
            L = rng.uniform(260, 620) * (0.5 + depth) * (1 if sgn == 1 else rng.uniform(0.3, 0.75))
            ray(acc, p[0], p[1], ang + rot + (0 if sgn == 1 else np.pi), L, int(9000 * (0.3 + depth)), 0.9 * depth + 0.08)
    if rng.random() < 0.3:
        faint_line(acc, p[0], p[1], base[rng.integers(3)] + rot, 5000, 0.10)
for ang in base:
    for sgn in (1, -1):
        L = rng.uniform(520, 700) * (1 if sgn == 1 else 0.6)
        ray(neon, NEON[0], NEON[1], ang + (0 if sgn == 1 else np.pi), L, 26000, 1.1)
faint_line(neon, NEON[0], NEON[1], base[0], 5000, 0.12)
n = 90000
acc[rng.integers(0, H, n), rng.integers(0, W, n)] += rng.uniform(0.05, 0.35, n).astype(np.float32)
def tone(buf):
    core = 1 - np.exp(-0.8 * buf)
    im = Image.fromarray(np.clip(core * 255, 0, 255).astype(np.uint8))
    bloom = (0.6 * np.asarray(im.filter(ImageFilter.GaussianBlur(4))) + 0.5 * np.asarray(im.filter(ImageFilter.GaussianBlur(22)))) / 255
    return np.clip(core + bloom, 0, 1)
v, vn = tone(acc), tone(neon)
bg = np.array([5, 5, 7.]); white = np.array([232, 233, 240.]); NC = np.array([0xEA, 0xFF, 0x3D], float)
img = bg + v[..., None] * (white - bg)
vg = np.clip(vn, 0, 1) ** 0.75                                         # neon is light: add it, do not mix it with black
img = img * (1 - vg[..., None]) + NC * vg[..., None]
hot = np.clip((vn - 0.9) / 0.1, 0, 1)                                  # a white-hot centre where the rays meet
img = img * (1 - 0.7 * hot[..., None]) + 250 * 0.7 * hot[..., None]
x = np.linspace(0, 1, W)[None, :]
t = np.clip((x - 0.56) / 0.16, 0, 1); t = t * t * (3 - 2 * t)
img = bg + (img - bg) * (1 - 0.92 * t)[..., None]   # the pattern runs edge to edge but recedes behind the text column
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save("cover_bg.png")
