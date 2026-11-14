"""Step 8 helper: a blind reading file of note pairs.

Sample (fixed seed) from the main-measure pair set (src/04 rules, gap <= 6h, links in both notes):
  - high source overlap (Jaccard >= 0.5): 15 AI-AI pairs, 15 human-human pairs
  - no shared source (Jaccard = 0): 5 AI-AI pairs, 5 human-human pairs
Pairs are shuffled and the order of the two notes is randomized. The reading file does not say
which group a pair is from; the key (results/reading/key.csv) does. Local only (gitignored):
it contains note text.
"""
import csv, random, tempfile
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
D, OUT = ROOT / "data" / "interim", ROOT / "results" / "reading"
random.seed(20261114)
con = duckdb.connect()
con.execute("SET memory_limit='2GB'; SET temp_directory='" + tempfile.gettempdir() + "/duckdb_tmp'")
con.execute(f"CREATE TABLE s AS SELECT * FROM '{D}/sample.parquet' WHERE len(urls) > 0")
rows = con.execute("""
SELECT a.tweetId, a.noteId, b.noteId, a.participantId, b.participantId,
  abs(a.createdAtMillis - b.createdAtMillis) / 60000.0 AS gap_min, a.lang,
  CASE WHEN a.is_fleet AND b.is_fleet THEN 'fleet-fleet' WHEN a.is_ai AND b.is_ai THEN 'AI-AI'
       WHEN a.is_ai OR b.is_ai THEN 'AI-human' ELSE 'human-human' END AS grp,
  len(list_intersect(a.urls, b.urls)) * 1.0 / len(list_distinct(list_concat(a.urls, b.urls))) AS j,
  a.text, a.urls, b.text, b.urls
FROM s a JOIN s b ON a.tweetId = b.tweetId AND a.noteId < b.noteId
  AND a.participantId <> b.participantId AND a.lang = b.lang
WHERE abs(a.createdAtMillis - b.createdAtMillis) <= 6 * 3600 * 1000""").fetchall()

pick = []
for grp in ("AI-AI", "human-human"):
    high = [r for r in rows if r[7] == grp and r[8] >= 0.5]
    low = [r for r in rows if r[7] == grp and r[8] == 0]
    pick += [(r, "high") for r in random.sample(high, 15)] + [(r, "none") for r in random.sample(low, 5)]
random.shuffle(pick)

def cut(t, n=450): return t if len(t) <= n else t[:n] + " ..."
with open(OUT / "pairs_to_read.md", "w") as f, open(OUT / "key.csv", "w", newline="") as k:
    kw = csv.writer(k); kw.writerow(["pair", "group", "sampled_as", "jaccard", "gap_min", "tweetId", "noteA", "noteB", "writerA", "writerB"])
    f.write("# Pairs to read (blind)\n\nTwo notes on the same post, written within 6 hours of each other, same language, both with sources. "
            "Text is lowercased and links are listed separately. Group labels are in key.csv; read first, look at the key after.\n\n"
            "For each pair, write down: do the two notes rest on the same evidence, or only sound alike? Is a shared source the obvious one for this claim, or a choice?\n")
    for n, (r, kind) in enumerate(pick, 1):
        tw, na, nb, pa, pb, gap, lang, grp, j, ta, ua, tb, ub = r
        if random.random() < 0.5: na, nb, pa, pb, ta, tb, ua, ub = nb, na, pb, pa, tb, ta, ub, ua
        kw.writerow([n, grp, kind, round(j, 3), round(gap, 1), tw, na, nb, pa[:8], pb[:8]])
        f.write(f"\n---\n\n## Pair {n}\n\npost: https://x.com/i/status/{tw}  |  gap: {gap:.0f} min  |  language: {lang}\n\n")
        for tag, t, u in (("A", ta, ua), ("B", tb, ub)):
            f.write(f"**Note {tag}:** {cut(t)}\n\nsources {tag}: " + ("  \n".join(u)) + "\n\n")
print(f"{len(pick)} pairs written to {OUT}/pairs_to_read.md")
