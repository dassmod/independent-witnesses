"""Extension F: robustness of the headline numbers to reasonable alternative settings.

Registered in docs/decisions.md (15 Nov). Recomputes (a) the source Jaccard difference AI-AI minus
human-human (human reweighted to the AI-AI time profile) and (b) the AI-AI share of pairs above the
human top-p text threshold, under alternative fleet definitions, n-gram size, threshold and windows.
Post weights and cluster bootstrap over posts (300 resamples) as in the main analysis.
"""
import csv, tempfile
from pathlib import Path
import duckdb, numpy as np

ROOT = Path(__file__).resolve().parents[1]
D, T = ROOT / "data" / "interim", ROOT / "results" / "tables"
B, SEED = 300, 20261114
con = duckdb.connect()
con.execute("SET memory_limit='2GB'; SET temp_directory='" + tempfile.gettempdir() + "/duckdb_tmp'")
con.execute(f"CREATE TABLE s AS SELECT * FROM '{D}/sample.parquet' WHERE length(text) >= 4")
ai_rank = [r[0] for r in con.execute("SELECT participantId FROM s WHERE is_ai GROUP BY 1 ORDER BY count(*) DESC").fetchall()]
fleet6 = set(r[0] for r in con.execute("SELECT DISTINCT participantId FROM s WHERE is_fleet").fetchall())
next_ai = [p for p in ai_rank if p not in fleet6][0]
rows = con.execute("""
SELECT a.tweetId, a.participantId, b.participantId, a.is_ai, b.is_ai,
  abs(a.createdAtMillis - b.createdAtMillis) / 60000.0, a.text, b.text,
  len(list_intersect(a.urls, b.urls)), len(list_distinct(list_concat(a.urls, b.urls))), len(a.urls) > 0 AND len(b.urls) > 0
FROM s a JOIN s b ON a.tweetId = b.tweetId AND a.noteId < b.noteId
 AND a.participantId <> b.participantId AND a.lang = b.lang
WHERE abs(a.createdAtMillis - b.createdAtMillis) <= 24 * 3600 * 1000""").fetchall()
def grams(t, n): return {t[i:i + n] for i in range(len(t) - n + 1)}
post = np.array([r[0] for r in rows]); pa = np.array([r[1] for r in rows]); pb = np.array([r[2] for r in rows])
aia = np.array([r[3] for r in rows]); aib = np.array([r[4] for r in rows]); gap = np.array([r[5] for r in rows])
j = {}
for n in (3, 4):
    j[n] = np.array([(lambda A, Bb: len(A & Bb) / len(A | Bb) if A | Bb else 0)(grams(r[6], n), grams(r[7], n)) for r in rows])
src = np.array([r[8] / r[9] if r[10] else np.nan for r in rows])
pid = {t: i for i, t in enumerate(sorted(set(post)))}; pi = np.array([pid[t] for t in post]); P = len(pid)
print(f"pairs {len(rows):,}, posts {P:,}", flush=True)

def run(fleet, n=4, top=0.05, bounds=(60, 360)):
    fa, fb = np.isin(pa, list(fleet)), np.isin(pb, list(fleet))
    grp = np.where(fa & fb, 3, np.where(aia & aib, 0, np.where(~aia & ~aib, 1, 2)))
    win = np.where(gap < bounds[0], 0, np.where(gap < bounds[1], 1, 2))
    key = pi * 4 + grp
    _, inv, c = np.unique(key, return_inverse=True, return_counts=True)
    w = 1.0 / c[inv]
    jj = j[n]
    def stat(mult):
        ww = w * mult[pi]
        thr = np.zeros(3)
        for k in range(3):
            m = (grp == 1) & (win == k); o = np.argsort(jj[m], kind="stable")
            cs = np.cumsum(ww[m][o]); thr[k] = jj[m][o][min(np.searchsorted(cs, (1 - top) * cs[-1]), m.sum() - 1)]
        above = jj > thr[win]
        W = np.array([[ww[(grp == g) & (win == k)].sum() for k in range(3)] for g in (0, 1)])
        prof = W[0] / W[0].sum()
        share = (np.array([(ww * above)[(grp == 0) & (win == k)].sum() for k in range(3)]) / W[0]) @ prof
        okm = ~np.isnan(src)
        sm = np.array([[(ww * np.nan_to_num(src))[(grp == g) & (win == k) & okm].sum() / ww[(grp == g) & (win == k) & okm].sum() for k in range(3)] for g in (0, 1)])
        Ws = np.array([ww[(grp == 0) & (win == k) & okm].sum() for k in range(3)]); ps = Ws / Ws.sum()
        return sm[0] @ ps - sm[1] @ ps, share
    pt = stat(np.ones(P))
    rng = np.random.default_rng(SEED)
    bt = np.array([stat(np.bincount(rng.integers(0, P, P), minlength=P).astype(float)) for _ in range(B)])
    lo, hi = np.percentile(bt, [2.5, 97.5], axis=0)
    return pt, lo, hi, int((grp == 0).sum())

variants = [("main: fleet = top 6, 4-gram, top 5%, windows 1h/6h", dict(fleet=fleet6)),
            ("fleet = top 7", dict(fleet=fleet6 | {next_ai})),
            ("no fleet merge (fleet-fleet counted as AI-AI)", dict(fleet=set())),
            ("3-gram", dict(fleet=fleet6, n=3)),
            ("threshold at human top 10%", dict(fleet=fleet6, top=0.10)),
            ("windows 30min / 3h", dict(fleet=fleet6, bounds=(30, 180)))]
with open(T / "extF_robustness.csv", "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["variant", "AI-AI pairs", "source_jaccard_diff", "lo", "hi", "AI-AI_text_above", "lo", "hi", "human_reference"])
    for name, kw in variants:
        (d, s), lo, hi, nai = run(**kw)
        ref = kw.get("top", 0.05)
        wr.writerow([name, nai, round(d, 4), round(lo[0], 4), round(hi[0], 4), round(s, 4), round(lo[1], 4), round(hi[1], 4), ref])
        print(f"{name:52s} AI-AI pairs {nai:6,d}  src diff {d:+.3f} [{lo[0]:+.3f}, {hi[0]:+.3f}]  text above {s:.3f} [{lo[1]:.3f}, {hi[1]:.3f}] vs human {ref}", flush=True)
