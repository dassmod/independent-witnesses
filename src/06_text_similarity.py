"""Secondary measure: text similarity (character 4-gram Jaccard) between notes on the same post.

Same pairs, windows and post weights as src/04 (docs/decisions.md), except that notes are not
required to contain a link (only >= 4 characters of text after removing links).
Headline: share of AI-AI pairs above the threshold set by the most similar 5% of human-human
pairs in the same time window (post-weighted). Under human-like independence this is about 5%.
The threshold is re-estimated inside every bootstrap resample.
"""
import csv, tempfile
from pathlib import Path
import duckdb, numpy as np

ROOT = Path(__file__).resolve().parents[1]
D, T = ROOT / "data" / "interim", ROOT / "results" / "tables"
B, SEED, TOP = 1000, 20261114, 0.05
GROUPS = ["AI-AI", "human-human", "AI-human", "fleet-fleet"]
WINS = ["lt1h", "1-6h", "6-24h"]

con = duckdb.connect()
con.execute("SET memory_limit='2GB'; SET temp_directory='" + tempfile.gettempdir() + "/duckdb_tmp'")
con.execute(f"CREATE TABLE s AS SELECT noteId, participantId, tweetId, createdAtMillis, is_ai, is_fleet, lang, text FROM '{D}/sample.parquet' WHERE length(text) >= 4")
cur = con.execute("""
WITH p AS (
  SELECT a.tweetId, abs(a.createdAtMillis - b.createdAtMillis) / 60000.0 AS gap_min,
    CASE WHEN a.is_fleet AND b.is_fleet THEN 'fleet-fleet' WHEN a.is_ai AND b.is_ai THEN 'AI-AI'
         WHEN a.is_ai OR b.is_ai THEN 'AI-human' ELSE 'human-human' END AS grp,
    a.text AS ta, b.text AS tb
  FROM s a JOIN s b ON a.tweetId = b.tweetId AND a.noteId < b.noteId
                   AND a.participantId <> b.participantId AND a.lang = b.lang
  WHERE abs(a.createdAtMillis - b.createdAtMillis) <= 24 * 3600 * 1000)
SELECT tweetId, grp, CASE WHEN gap_min < 60 THEN 0 WHEN gap_min < 360 THEN 1 ELSE 2 END AS win,
       1.0 / count(*) OVER (PARTITION BY tweetId, grp) AS w, ta, tb FROM p""")

def grams(t): return {t[i:i + 4] for i in range(len(t) - 3)}
post_ids, pi, gi, wi, w, tj = {}, [], [], [], [], []
while True:
    rows = cur.fetchmany(20_000)
    if not rows: break
    for tw, g, win, wt, ta, tb in rows:
        A, Bset = grams(ta), grams(tb)
        pi.append(post_ids.setdefault(tw, len(post_ids))); gi.append(GROUPS.index(g)); wi.append(win)
        w.append(wt); tj.append(len(A & Bset) / len(A | Bset))
pi, gi, wi, w, tj = map(np.array, (pi, gi, wi, w, tj))
P = len(post_ids)
print(f"pairs: {len(w):,}, posts: {P:,}", flush=True)

cells = {(g, k): np.where((gi == g) & (wi == k))[0] for g in range(4) for k in range(3)}
HH = GROUPS.index("human-human")
hh_order = {k: cells[(HH, k)][np.argsort(tj[cells[(HH, k)]], kind="stable")] for k in range(3)}

def evaluate(mult):
    eff = w * mult[pi]
    thr = np.zeros(3)
    for k in range(3):
        idx = hh_order[k]; cum = np.cumsum(eff[idx])
        thr[k] = tj[idx][min(np.searchsorted(cum, (1 - TOP) * cum[-1]), len(idx) - 1)]
    above = np.zeros((4, 3)); tot = np.zeros((4, 3)); mean = np.zeros((4, 3))
    for (g, k), idx in cells.items():
        e = eff[idx]; tot[g, k] = e.sum()
        above[g, k] = e[tj[idx] > thr[k]].sum(); mean[g, k] = (e * tj[idx]).sum() / max(tot[g, k], 1e-12)
    with np.errstate(invalid="ignore", divide="ignore"):
        return thr, above / tot, above.sum(1) / tot.sum(1), mean

point = evaluate(np.ones(P))
rng = np.random.default_rng(SEED)
boots = [evaluate(np.bincount(rng.integers(0, P, P), minlength=P).astype(float)) for _ in range(B)]
ci = lambda j: np.nanpercentile(np.array([b[j] for b in boots]), [2.5, 97.5], axis=0)
(c_share, c_pool, c_mean) = ci(1), ci(2), ci(3)

npairs = {(g, k): len(i) for (g, k), i in cells.items()}
nposts = {(g, k): len(set(pi[i])) for (g, k), i in cells.items()}
with open(T / "step5_text_cells.csv", "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["group", "window", "pairs", "posts", "mean_4gram_jaccard", "mean_lo", "mean_hi",
                 "share_above_human_top5pct", "share_lo", "share_hi", "threshold"])
    for g in range(4):
        for k in range(3):
            wr.writerow([GROUPS[g], WINS[k], npairs[g, k], nposts[g, k],
                         *[round(float(x), 4) for x in (point[3][g, k], c_mean[0][g, k], c_mean[1][g, k],
                                                          point[1][g, k], c_share[0][g, k], c_share[1][g, k], point[0][k])]])
with open(T / "step5_text_main.csv", "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["group", "share_above_human_top5pct", "lo", "hi"])
    for g in range(4):
        wr.writerow([GROUPS[g], *[round(float(x), 4) for x in (point[2][g], c_pool[0][g], c_pool[1][g])]])

print("\nthresholds (4-gram Jaccard of the 95th percentile of human-human pairs):", [round(float(x), 3) for x in point[0]])
print(f"\n{'group':12s} {'window':7s} {'pairs':>8s}  {'mean text sim':>13s}  {'share above human top 5%':>26s}")
for g in range(4):
    for k in range(3):
        print(f"{GROUPS[g]:12s} {WINS[k]:7s} {npairs[g,k]:8,d}  {point[3][g,k]:13.3f}  {point[1][g,k]:8.3f} [{c_share[0][g,k]:.3f}, {c_share[1][g,k]:.3f}]")
print("\nPOOLED over the three windows (share of pairs above the human top-5% threshold; human is 5% by construction)")
for g in range(4):
    print(f"  {GROUPS[g]:12s} {point[2][g]:.3f}  95% CI [{c_pool[0][g]:.3f}, {c_pool[1][g]:.3f}]")
