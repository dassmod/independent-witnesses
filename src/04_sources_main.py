"""Steps 3-6 for the main measure: shared sources between notes on the same post.

Follows docs/decisions.md. Pairs: different participants, same post, same language,
both notes keep >=1 source URL, time gap <= 24h. Windows: <1h, 1-6h, 6-24h.
Every post weighs the same inside a group: pair weight = 1 / (pairs of its group on that post).
Main number: AI-AI (fleet = one author, so fleet-internal pairs are their own group)
minus human-human reweighted to the AI-AI time profile. Cluster bootstrap over posts.
"""
import csv, sys, tempfile
from pathlib import Path
import duckdb, numpy as np

ROOT = Path(__file__).resolve().parents[1]
D, T = ROOT / "data" / "interim", ROOT / "results" / "tables"
B, SEED = 1000, 20261114
LANG = sys.argv[1] if len(sys.argv) > 1 else None   # optional: keep only pairs in this language, e.g. "en"
SUF = f"_{LANG}" if LANG else ""

con = duckdb.connect()
con.execute("SET memory_limit='2GB'; SET temp_directory='" + tempfile.gettempdir() + "/duckdb_tmp'")
con.execute(f"CREATE TABLE s AS SELECT * FROM '{D}/sample.parquet' WHERE len(urls) > 0")
con.execute(f"""
CREATE TABLE p AS
SELECT a.tweetId,
  abs(a.createdAtMillis - b.createdAtMillis) / 60000.0 AS gap_min,
  CASE WHEN a.is_fleet AND b.is_fleet THEN 'fleet-fleet'
       WHEN a.is_ai AND b.is_ai THEN 'AI-AI'
       WHEN a.is_ai OR b.is_ai THEN 'AI-human' ELSE 'human-human' END AS grp,
  len(list_intersect(a.urls, b.urls)) AS inter,
  len(list_distinct(list_concat(a.urls, b.urls))) AS uni
FROM s a JOIN s b ON a.tweetId = b.tweetId AND a.noteId < b.noteId
                 AND a.participantId <> b.participantId AND a.lang = b.lang
                 {("AND a.lang = '" + LANG + "'") if LANG else ''}
WHERE abs(a.createdAtMillis - b.createdAtMillis) <= 24 * 3600 * 1000""")
con.execute("""
CREATE TABLE pw AS
SELECT *, inter * 1.0 / uni AS j, (inter > 0)::INT AS any_shared,
  CASE WHEN gap_min < 60 THEN 'lt1h' WHEN gap_min < 360 THEN '1-6h' ELSE '6-24h' END AS win,
  1.0 / count(*) OVER (PARTITION BY tweetId, grp) AS w
FROM p""")

GROUPS = ["AI-AI", "human-human", "AI-human", "fleet-fleet"]
WINS = ["lt1h", "1-6h", "6-24h", "lt1min"]          # lt1min is a slice of lt1h, reported separately
rows = con.execute("""
SELECT tweetId, grp, win_ AS win, sum(w) AS W, sum(w*j) AS WJ, sum(w*any_shared) AS WA, count(*) AS N
FROM (SELECT *, win AS win_ FROM pw UNION ALL SELECT *, 'lt1min' FROM pw WHERE gap_min < 1)
GROUP BY ALL""").fetchall()
posts = {t: i for i, t in enumerate(sorted({r[0] for r in rows}))}
P = len(posts)
stats = np.zeros((P, len(GROUPS), len(WINS), 3))   # W, W*J, W*any
npairs = np.zeros((len(GROUPS), len(WINS)), dtype=int)
nposts = np.zeros((len(GROUPS), len(WINS)), dtype=int)
for t, g, w, W, WJ, WA, N in rows:
    gi, wi = GROUPS.index(g), WINS.index(w)
    stats[posts[t], gi, wi] = (W, WJ, WA)
    npairs[gi, wi] += N; nposts[gi, wi] += 1

def summarize(tot):
    """tot: (G, Wn, 3) summed stats -> cell means, pooled means, overall difference."""
    W, WJ, WA = tot[..., 0], tot[..., 1], tot[..., 2]
    with np.errstate(invalid="ignore", divide="ignore"):
        cell = np.stack([WJ / W, WA / W], -1)                       # (G, Wn, 2) means per cell
        main = slice(0, 3)
        pooled = np.stack([WJ[:, main].sum(1) / W[:, main].sum(1),
                           WA[:, main].sum(1) / W[:, main].sum(1)], -1)   # (G, 2)
        ai, hh = GROUPS.index("AI-AI"), GROUPS.index("human-human")
        prof = W[ai, main] / W[ai, main].sum()                        # AI-AI time profile
        hh_rew = (prof[:, None] * cell[hh, main]).sum(0)              # human-human reweighted to it
        diff = pooled[ai] - hh_rew                                    # (2,)
        cell_diff = cell[ai, main] - cell[hh, main]                   # (3, 2)
    return cell, pooled, hh_rew, diff, cell_diff

point = summarize(stats.sum(0))
rng = np.random.default_rng(SEED)
boot = [summarize(np.tensordot(np.bincount(rng.integers(0, P, P), minlength=P), stats, axes=(0, 0)))
        for _ in range(B)]
ci = lambda k, idx=(): np.nanpercentile(np.array([b[k] for b in boot]), [2.5, 97.5], axis=0)

# ---- tables
T.mkdir(parents=True, exist_ok=True)
with open(T / f"step4_cells{SUF}.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["group", "window", "pairs", "posts", "jaccard", "jaccard_lo", "jaccard_hi", "any_shared", "any_lo", "any_hi"])
    cl, ch = ci(0)
    for gi, g in enumerate(GROUPS):
        for wi, win in enumerate(WINS):
            w.writerow([g, win, npairs[gi, wi], nposts[gi, wi],
                        *[round(x, 4) for x in (point[0][gi, wi, 0], cl[gi, wi, 0], ch[gi, wi, 0],
                                                  point[0][gi, wi, 1], cl[gi, wi, 1], ch[gi, wi, 1])]])
dlo, dhi = ci(3)
with open(T / f"step4_main{SUF}.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["measure", "AI-AI_pooled", "human-human_reweighted", "difference", "ci_lo", "ci_hi", "bootstrap_resamples", "posts_resampled"])
    for k, name in enumerate(["jaccard", "any_shared"]):
        w.writerow([name, *[round(float(x), 4) for x in (point[1][GROUPS.index("AI-AI"), k], point[2][k], point[3][k], dlo[k], dhi[k])], B, P])

# ---- print
print(f"pairs in analysis: {int(npairs[:, :3].sum()):,}; posts: {P:,}\n")
print(f"{'group':12s} {'window':7s} {'pairs':>8s} {'posts':>7s}  {'Jaccard':>8s} [{'95% CI':^15s}]  {'any shared':>10s}")
cl, ch = ci(0)
for gi, g in enumerate(GROUPS):
    for wi, win in enumerate(WINS):
        if npairs[gi, wi]:
            print(f"{g:12s} {win:7s} {npairs[gi,wi]:8,d} {nposts[gi,wi]:7,d}  {point[0][gi,wi,0]:8.3f} [{cl[gi,wi,0]:.3f}, {ch[gi,wi,0]:.3f}]  {point[0][gi,wi,1]:10.3f}")
print("\nMAIN: AI-AI minus human-human (reweighted to AI-AI time profile)")
for k, name in enumerate(["Jaccard", "any shared"]):
    print(f"  {name:11s} AI-AI {point[1][GROUPS.index('AI-AI'), k]:.3f}  human {point[2][k]:.3f}  diff {point[3][k]:+.3f}  95% CI [{dlo[k]:+.3f}, {dhi[k]:+.3f}]")
