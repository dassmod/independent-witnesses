"""How often are two notes on the same post copies of each other?

Same pairs as src/06 (same post, different authors, same language, gap <= 24h, >= 4 chars of text).
Exact copy: identical text after lowercasing and removing links.
Near copy: character 4-gram Jaccard >= 0.8.
Shares are post-weighted (each post weighs the same inside a group); raw counts alongside.
"""
import csv, tempfile
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
D, T = ROOT / "data" / "interim", ROOT / "results" / "tables"
con = duckdb.connect()
con.execute("SET memory_limit='2GB'; SET temp_directory='" + tempfile.gettempdir() + "/duckdb_tmp'")
con.execute(f"CREATE TABLE s AS SELECT noteId, participantId, tweetId, createdAtMillis, is_ai, is_fleet, lang, text FROM '{D}/sample.parquet' WHERE length(text) >= 4")
con.create_function("g4j", lambda a, b: (lambda A, B: len(A & B) / len(A | B))({a[i:i+4] for i in range(len(a)-3)}, {b[i:i+4] for i in range(len(b)-3)}), ["VARCHAR", "VARCHAR"], "DOUBLE")
con.execute("""
CREATE TABLE p AS
SELECT a.tweetId,
  CASE WHEN a.is_fleet AND b.is_fleet THEN 'fleet-fleet' WHEN a.is_ai AND b.is_ai THEN 'AI-AI'
       WHEN a.is_ai OR b.is_ai THEN 'AI-human' ELSE 'human-human' END AS grp,
  abs(a.createdAtMillis - b.createdAtMillis) / 60000.0 AS gap_min,
  (a.text = b.text)::INT AS exact, g4j(a.text, b.text) AS j
FROM s a JOIN s b ON a.tweetId = b.tweetId AND a.noteId < b.noteId
 AND a.participantId <> b.participantId AND a.lang = b.lang
WHERE abs(a.createdAtMillis - b.createdAtMillis) <= 24 * 3600 * 1000""")
sql = """
SELECT grp, count(*) AS pairs, sum(exact) AS exact_n, sum((j >= 0.8)::INT) AS near_n,
  round(100 * sum(w * exact) / sum(w), 2) AS exact_pct_postw,
  round(100 * sum(w * (j >= 0.8)::INT) / sum(w), 2) AS near_pct_postw,
  round(median(gap_min) FILTER (WHERE j >= 0.8), 1) AS near_median_gap_min
FROM (SELECT *, 1.0 / count(*) OVER (PARTITION BY tweetId, grp) AS w FROM p) GROUP BY 1 ORDER BY 1"""
con.execute(f"COPY ({sql}) TO '{T}/step8_copies.csv' (HEADER)")
con.sql(sql).show()
print("near copies by gap window (post-weighted %)")
con.sql("""SELECT grp, round(100*sum(w*(j>=0.8)::INT) FILTER (WHERE gap_min<60)/sum(w) FILTER (WHERE gap_min<60),2) lt1h,
  round(100*sum(w*(j>=0.8)::INT) FILTER (WHERE gap_min>=60 AND gap_min<360)/sum(w) FILTER (WHERE gap_min>=60 AND gap_min<360),2) "1-6h",
  round(100*sum(w*(j>=0.8)::INT) FILTER (WHERE gap_min>=360)/sum(w) FILTER (WHERE gap_min>=360),2) "6-24h"
  FROM (SELECT *, 1.0/count(*) OVER (PARTITION BY tweetId, grp) w FROM p) GROUP BY 1 ORDER BY 1""").show()
