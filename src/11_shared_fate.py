"""Extension B: do two notes on the same post share their fate?

Registered in docs/decisions.md (15 Nov). Pairs as in the main measure, no link requirement;
only pairs where both notes have a decided currentStatus (helpful = 1, not helpful = 0).
Phi for unordered pairs: (P(both 1) - p^2) / (p (1 - p)), p = mean outcome over both notes,
from post-weighted counts. Human-human windows reweighted to the AI-AI time profile.
Cluster bootstrap over posts. Secondary: concordance inside AI-AI pairs by similarity.
"""
import csv, tempfile
from pathlib import Path
import duckdb, numpy as np

ROOT = Path(__file__).resolve().parents[1]
D, T = ROOT / "data" / "interim", ROOT / "results" / "tables"
B, SEED = 1000, 20261114
GROUPS = ["AI-AI", "human-human", "AI-human", "fleet-fleet"]
thr = {}
for r in csv.DictReader(open(T / "step5_text_cells.csv")):
    if r["group"] == "human-human": thr[r["window"]] = float(r["threshold"])

con = duckdb.connect()
con.execute("SET memory_limit='2GB'; SET temp_directory='" + tempfile.gettempdir() + "/duckdb_tmp'")
con.execute(f"""CREATE TABLE s AS SELECT x.*, (st.currentStatus = 'CURRENTLY_RATED_HELPFUL')::INT AS y
  FROM '{D}/sample.parquet' x JOIN '{D}/status.parquet' st USING (noteId)
  WHERE st.currentStatus IN ('CURRENTLY_RATED_HELPFUL', 'CURRENTLY_RATED_NOT_HELPFUL')""")
rows = con.execute("""
WITH p AS (
  SELECT a.tweetId, abs(a.createdAtMillis - b.createdAtMillis) / 60000.0 AS gap,
    CASE WHEN a.is_fleet AND b.is_fleet THEN 'fleet-fleet' WHEN a.is_ai AND b.is_ai THEN 'AI-AI'
         WHEN a.is_ai OR b.is_ai THEN 'AI-human' ELSE 'human-human' END AS grp,
    a.y AS ya, b.y AS yb, a.text AS ta, b.text AS tb, len(list_intersect(a.urls, b.urls)) > 0 AS shared
  FROM s a JOIN s b ON a.tweetId = b.tweetId AND a.noteId < b.noteId
   AND a.participantId <> b.participantId AND a.lang = b.lang
  WHERE abs(a.createdAtMillis - b.createdAtMillis) <= 24 * 3600 * 1000)
SELECT tweetId, grp, CASE WHEN gap < 60 THEN 0 WHEN gap < 360 THEN 1 ELSE 2 END AS win,
  1.0 / count(*) OVER (PARTITION BY tweetId, grp) AS w, ya, yb, ta, tb, shared FROM p""").fetchall()

posts = {t: i for i, t in enumerate(sorted({r[0] for r in rows}))}
P = len(posts)
S = np.zeros((P, 4, 3, 3))           # per post, group, window: W, W*both1, W*mean outcome
N = np.zeros((4, 3), dtype=int); nposts = [set() for _ in range(4)]
sec = []
def g4(t): return {t[i:i + 4] for i in range(len(t) - 3)}
for tw, g, win, w, ya, yb, ta, tb, shared in rows:
    gi = GROUPS.index(g)
    S[posts[tw], gi, win] += (w, w * ya * yb, w * (ya + yb) / 2)
    N[gi, win] += 1; nposts[gi].add(tw)
    if g == "AI-AI":
        A_, B_ = g4(ta or ""), g4(tb or "")
        j = len(A_ & B_) / len(A_ | B_) if A_ | B_ else 0
        sec.append((int(ya == yb), j > thr[["lt1h", "1-6h", "6-24h"][win]], bool(shared)))

def phis(tot):
    W, B11, B1 = tot[..., 0], tot[..., 1], tot[..., 2]
    ai, hh = 0, 1
    prof = W[ai] / W[ai].sum()
    out = np.zeros(4)
    for g in range(4):
        if g == hh:   # reweight human windows to the AI-AI time profile
            k = np.divide(prof, W[hh] / W[hh].sum(), out=np.zeros(3), where=W[hh] > 0)
            Wg, Bg11, Bg1 = (W[g] * k).sum(), (B11[g] * k).sum(), (B1[g] * k).sum()
        else:
            Wg, Bg11, Bg1 = W[g].sum(), B11[g].sum(), B1[g].sum()
        p, p11 = Bg1 / Wg, Bg11 / Wg
        out[g] = (p11 - p * p) / (p * (1 - p))
    return out

point = phis(S.sum(0))
rng = np.random.default_rng(SEED)
boot = np.array([phis(np.tensordot(np.bincount(rng.integers(0, P, P), minlength=P), S, axes=(0, 0))) for _ in range(B)])
lo, hi = np.nanpercentile(boot, [2.5, 97.5], axis=0)
d = boot[:, 0] - boot[:, 1]; dlo, dhi = np.nanpercentile(d, [2.5, 97.5])
helpful_share = S.sum(0)[..., 2].sum(1) / S.sum(0)[..., 0].sum(1)

with open(T / "extB_shared_fate.csv", "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["group", "pairs", "posts", "share_helpful", "phi", "phi_lo", "phi_hi"])
    for g in range(4):
        wr.writerow([GROUPS[g], int(N[g].sum()), len(nposts[g]), round(float(helpful_share[g]), 4),
                     round(float(point[g]), 4), round(float(lo[g]), 4), round(float(hi[g]), 4)])
    wr.writerow(["AI-AI minus human-human", "", "", "", round(float(point[0] - point[1]), 4), round(float(dlo), 4), round(float(dhi), 4)])
print(f"posts: {P:,}\n{'group':12s} {'pairs':>6s} {'posts':>6s} {'helpful':>8s}  {'phi':>6s} [95% CI]")
for g in range(4):
    print(f"{GROUPS[g]:12s} {N[g].sum():6d} {len(nposts[g]):6d} {helpful_share[g]:8.3f}  {point[g]:6.3f} [{lo[g]:.3f}, {hi[g]:.3f}]")
print(f"\nMAIN: phi(AI-AI) - phi(human-human) = {point[0]-point[1]:+.3f}  95% CI [{dlo:+.3f}, {dhi:+.3f}]")
sec = np.array(sec, dtype=float)
print("\nSecondary, AI-AI pairs (unweighted): share with the same outcome")
for name, col in (("text above human top-5% threshold", 1), ("shared source", 2)):
    m = sec[:, col] == 1
    print(f"  {name:34s} yes: {sec[m,0].mean():.3f} (n={int(m.sum())})   no: {sec[~m,0].mean():.3f} (n={int((~m).sum())})")
