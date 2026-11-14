"""Extension C: AI-AI similarity over time.

Registered in docs/decisions.md (15 Nov). Pairs as in src/04 (sources, links required) and
src/06 (text). Grouped by the creation month of the later note. Post-weighted within each
group and month. Registered test: AI-AI in Jul-Nov 2026 vs Nov 2025-Mar 2026, bootstrap over posts.
Also reports the share of AI-AI pairs under 1 hour per month (the time mix shifts).
"""
import csv, tempfile
from pathlib import Path
import duckdb, numpy as np

ROOT = Path(__file__).resolve().parents[1]
D, T = ROOT / "data" / "interim", ROOT / "results" / "tables"
B, SEED = 1000, 20261114
thr = {r["window"]: float(r["threshold"]) for r in csv.DictReader(open(T / "step5_text_cells.csv")) if r["group"] == "human-human"}
WIN = ["lt1h", "1-6h", "6-24h"]
EARLY, LATE = ("2025-11", "2026-03"), ("2026-07", "2026-11")

con = duckdb.connect()
con.execute("SET memory_limit='2GB'; SET temp_directory='" + tempfile.gettempdir() + "/duckdb_tmp'")
con.execute(f"CREATE TABLE s AS SELECT * FROM '{D}/sample.parquet' WHERE length(text) >= 4")
cur = con.execute("""
WITH p AS (
  SELECT a.tweetId, abs(a.createdAtMillis - b.createdAtMillis) / 60000.0 AS gap,
    strftime(to_timestamp(greatest(a.createdAtMillis, b.createdAtMillis) / 1000), '%Y-%m') AS month,
    CASE WHEN a.is_fleet AND b.is_fleet THEN 'fleet-fleet' WHEN a.is_ai AND b.is_ai THEN 'AI-AI'
         WHEN a.is_ai OR b.is_ai THEN 'AI-human' ELSE 'human-human' END AS grp,
    a.text AS ta, b.text AS tb, a.urls AS ua, b.urls AS ub
  FROM s a JOIN s b ON a.tweetId = b.tweetId AND a.noteId < b.noteId
   AND a.participantId <> b.participantId AND a.lang = b.lang
  WHERE abs(a.createdAtMillis - b.createdAtMillis) <= 24 * 3600 * 1000)
SELECT tweetId, grp, month, CASE WHEN gap < 60 THEN 0 WHEN gap < 360 THEN 1 ELSE 2 END AS win,
  1.0 / count(*) OVER (PARTITION BY tweetId, grp) AS w, ta, tb, ua, ub FROM p WHERE grp <> 'AI-human'""")
def g4(t): return {t[i:i + 4] for i in range(len(t) - 3)}
recs = []
while True:
    rows = cur.fetchmany(20_000)
    if not rows: break
    for tw, g, m, win, w, ta, tb, ua, ub in rows:
        A_, B_ = g4(ta), g4(tb)
        above = (len(A_ & B_) / len(A_ | B_)) > thr[WIN[win]]
        has = bool(ua) and bool(ub)
        jac = len(set(ua) & set(ub)) / len(set(ua) | set(ub)) if has else np.nan
        recs.append((tw, g, m, win, w, above, jac))

import collections
agg = collections.defaultdict(lambda: np.zeros(6))   # W_text, W*above, W_src, W*jac, n, n_lt1h
for tw, g, m, win, w, above, jac in recs:
    a = agg[(g, m)]; a[0] += w; a[1] += w * above; a[4] += 1; a[5] += (win == 0)
    if not np.isnan(jac): a[2] += w; a[3] += w * jac
months = sorted({m for _, m in agg})
with open(T / "extC_monthly.csv", "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["group", "month", "pairs", "share_lt1h", "source_jaccard", "text_above_threshold"])
    for g in ("AI-AI", "fleet-fleet", "human-human"):
        for m in months:
            a = agg.get((g, m))
            if a is None or a[4] < 30: continue
            wr.writerow([g, m, int(a[4]), round(a[5] / a[4], 3), round(a[3] / a[2], 4) if a[2] else "", round(a[1] / a[0], 4)])
print(open(T / "extC_monthly.csv").read())

# registered test: AI-AI late vs early, bootstrap over posts
ai = [r for r in recs if r[1] == "AI-AI" and (EARLY[0] <= r[2] <= EARLY[1] or LATE[0] <= r[2] <= LATE[1])]
pid = {t: i for i, t in enumerate(sorted({r[0] for r in ai}))}
M = np.zeros((len(pid), 2, 4))   # post, period, (W_text, W*above, W_src, W*jac)
for tw, g, m, win, w, above, jac in ai:
    k = 1 if m >= LATE[0] else 0
    M[pid[tw], k, 0] += w; M[pid[tw], k, 1] += w * above
    if not np.isnan(jac): M[pid[tw], k, 2] += w; M[pid[tw], k, 3] += w * jac
def diffs(t): return np.array([t[1, 3] / t[1, 2] - t[0, 3] / t[0, 2], t[1, 1] / t[1, 0] - t[0, 1] / t[0, 0]])
pt = diffs(M.sum(0)); tot = M.sum(0)
rng = np.random.default_rng(SEED)
bt = np.array([diffs(np.tensordot(np.bincount(rng.integers(0, len(pid), len(pid)), minlength=len(pid)), M, axes=(0, 0))) for _ in range(B)])
lo, hi = np.percentile(bt, [2.5, 97.5], axis=0)
with open(T / "extC_trend_test.csv", "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["measure", "early_Nov25_Mar26", "late_Jul_Nov26", "difference", "ci_lo", "ci_hi"])
    for k, (name, a, b) in enumerate((("source_jaccard", 3, 2), ("text_above_threshold", 1, 0))):
        wr.writerow([name, round(tot[0, a] / tot[0, b], 4), round(tot[1, a] / tot[1, b], 4), round(pt[k], 4), round(lo[k], 4), round(hi[k], 4)])
print(open(T / "extC_trend_test.csv").read())
