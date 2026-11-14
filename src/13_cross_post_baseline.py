"""Extension D: cross-post baseline, separating shared style from shared content.

Registered in docs/decisions.md (15 Nov). Within-post pairs as in src/04 and src/06 (fleet counted
as one author, so fleet-fleet pairs are left out). Cross-post pairs: same group, same language,
same UTC day, different posts and authors, made by shuffling each (day, language, group) bucket
with a fixed seed and pairing neighbours. Excess = within minus cross, pooled over time windows
with the AI-AI within-post profile. Bootstrap: within by post, cross by pair.
"""
import csv, random, tempfile
from collections import defaultdict
from pathlib import Path
import duckdb, numpy as np

ROOT = Path(__file__).resolve().parents[1]
D, T = ROOT / "data" / "interim", ROOT / "results" / "tables"
B, SEED = 500, 20261114
thr = {r["window"]: float(r["threshold"]) for r in csv.DictReader(open(T / "step5_text_cells.csv")) if r["group"] == "human-human"}
WIN = ["lt1h", "1-6h", "6-24h"]
G = ["AI-AI", "human-human"]

con = duckdb.connect()
con.execute("SET memory_limit='2GB'; SET temp_directory='" + tempfile.gettempdir() + "/duckdb_tmp'")
notes = con.execute(f"""
SELECT noteId, CASE WHEN is_fleet THEN 'FLEET' ELSE participantId END AS author, is_ai, tweetId,
       createdAtMillis, lang, text, urls, strftime(to_timestamp(createdAtMillis / 1000), '%Y-%m-%d') AS day
FROM '{D}/sample.parquet' WHERE length(text) >= 4 ORDER BY noteId""").fetchall()

def g4(t): return {t[i:i + 4] for i in range(len(t) - 3)}
def win_of(gap_min): return 0 if gap_min < 60 else 1 if gap_min < 360 else 2
def measures(a, b):
    A_, B_ = g4(a[6]), g4(b[6])
    j4 = len(A_ & B_) / len(A_ | B_)
    gap = abs(a[4] - b[4]) / 60000
    w = win_of(gap)
    ua, ub = set(a[7]), set(b[7])
    src = len(ua & ub) / len(ua | ub) if ua and ub else np.nan
    return w, float(j4 > thr[WIN[w]]), j4, src

# within-post pairs
by_post = defaultdict(list)
for n in notes: by_post[n[3]].append(n)
within = []   # (group, post, window, above, j4, src)
for tw, ns in by_post.items():
    for i in range(len(ns)):
        for k in range(i + 1, len(ns)):
            a, b = ns[i], ns[k]
            if a[1] == b[1] or a[5] != b[5] or abs(a[4] - b[4]) > 24 * 3600 * 1000: continue
            if a[2] and b[2]: g = 0
            elif not a[2] and not b[2]: g = 1
            else: continue
            within.append((g, tw, *measures(a, b)))
cnt = defaultdict(int)
for r in within: cnt[(r[0], r[1])] += 1

# cross-post pairs
rnd = random.Random(SEED)
buckets = defaultdict(list)
for n in notes: buckets[(n[8], n[5], n[2])].append(n)
cross = []    # (group, window, above, j4, src)
for key in sorted(buckets):
    ns = buckets[key][:]; rnd.shuffle(ns)
    for i in range(0, len(ns) - 1, 2):
        a, b = ns[i], ns[i + 1]
        if a[3] == b[3] or a[1] == b[1]: continue
        cross.append((0 if a[2] else 1, *measures(a, b)))
print(f"within-post pairs: AI-AI {sum(r[0]==0 for r in within):,}, human {sum(r[0]==1 for r in within):,}; "
      f"cross-post pairs: AI-AI {sum(r[0]==0 for r in cross):,}, human {sum(r[0]==1 for r in cross):,}", flush=True)

# arrays
Wg = np.array([r[0] for r in within]); Wp = np.array([r[1] for r in within]); Ww = np.array([r[2] for r in within])
Wv = np.array([[r[3], r[4], r[5]] for r in within]); Wwt = np.array([1.0 / cnt[(r[0], r[1])] for r in within])
pid = {t: i for i, t in enumerate(sorted(set(Wp)))}; Wpi = np.array([pid[t] for t in Wp])
Cg = np.array([r[0] for r in cross]); Cw = np.array([r[1] for r in cross]); Cv = np.array([[r[2], r[3], r[4]] for r in cross])

def cell_means(g, w, v, wt):
    out = np.full((2, 3, 3), np.nan); tot = np.zeros((2, 3))
    for gi in range(2):
        for wi in range(3):
            m = (g == gi) & (w == wi)
            tot[gi, wi] = wt[m].sum()
            for k in range(3):
                ok = m & ~np.isnan(v[:, k])
                if wt[ok].sum() > 0: out[gi, wi, k] = (wt[ok] * v[ok, k]).sum() / wt[ok].sum()
    return out, tot

def pooled(within_mult, cross_idx):
    wm, wtot = cell_means(Wg, Ww, Wv, Wwt * within_mult)
    cm, _ = cell_means(Cg[cross_idx], Cw[cross_idx], Cv[cross_idx], np.ones(len(cross_idx)))
    prof = wtot[0] / wtot[0].sum()
    W_ = np.einsum("w,gwk->gk", prof, wm); C_ = np.einsum("w,gwk->gk", prof, cm)
    return W_, C_, (W_ - C_)

pw, pc, pe = pooled(np.ones(len(Wg)), np.arange(len(Cg)))
rng = np.random.default_rng(SEED)
bw, bc, be, bd = [], [], [], []
P = len(pid)
for _ in range(B):
    mult = np.bincount(rng.integers(0, P, P), minlength=P)[Wpi].astype(float)
    idx = rng.integers(0, len(Cg), len(Cg))
    W_, C_, E_ = pooled(mult, idx)
    bw.append(W_); bc.append(C_); be.append(E_); bd.append(E_[0] - E_[1])
ci = lambda a: np.nanpercentile(np.array(a), [2.5, 97.5], axis=0)
(wl, wh), (cl, ch), (el, eh), (dl, dh) = ci(bw), ci(bc), ci(be), ci(bd)

names = ["text above human top-5%", "mean 4-gram Jaccard", "source Jaccard"]
with open(T / "extD_cross_post.csv", "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["measure", "group", "within_post", "w_lo", "w_hi", "cross_post", "c_lo", "c_hi", "excess", "e_lo", "e_hi"])
    for k, nm in enumerate(names):
        for gi in range(2):
            wr.writerow([nm, G[gi], *[round(float(x), 4) for x in (pw[gi,k], wl[gi,k], wh[gi,k], pc[gi,k], cl[gi,k], ch[gi,k], pe[gi,k], el[gi,k], eh[gi,k])]])
        wr.writerow([nm, "AI-AI excess minus human excess", "", "", "", "", "", "", round(float(pe[0,k]-pe[1,k]), 4), round(float(dl[k]), 4), round(float(dh[k]), 4)])
for k, nm in enumerate(names):
    print(f"\n== {nm}")
    for gi in range(2):
        print(f"  {G[gi]:12s} within {pw[gi,k]:.3f}  cross {pc[gi,k]:.3f} [{cl[gi,k]:.3f}, {ch[gi,k]:.3f}]  excess {pe[gi,k]:+.3f} [{el[gi,k]:+.3f}, {eh[gi,k]:+.3f}]")
    print(f"  AI-AI excess minus human excess: {pe[0,k]-pe[1,k]:+.3f} [{dl[k]:+.3f}, {dh[k]:+.3f}]")
