"""Check: do the AI writers outside the fleet look like one or more further operators?

For every non-fleet AI writer: volume, first note, and how often another AI writer
posts on the same post within one minute. Then the busiest pairs of non-fleet AI writers.
"""
import tempfile
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "interim"
con = duckdb.connect()
con.execute("SET memory_limit='2GB'; SET temp_directory='" + tempfile.gettempdir() + "/duckdb_tmp'")
con.execute(f"""CREATE TABLE a AS SELECT noteId, participantId, tweetId, createdAtMillis, is_fleet
                FROM '{D}/sample.parquet' WHERE is_ai""")
print("== non-fleet AI writers in the sample")
con.sql("""
WITH x AS (SELECT n.participantId, n.noteId, n.tweetId,
  EXISTS (SELECT 1 FROM a m WHERE m.tweetId = n.tweetId AND m.participantId <> n.participantId
          AND abs(m.createdAtMillis - n.createdAtMillis) < 60000) AS sync_any_ai,
  EXISTS (SELECT 1 FROM a m WHERE m.tweetId = n.tweetId AND m.is_fleet
          AND abs(m.createdAtMillis - n.createdAtMillis) < 60000) AS sync_fleet
  FROM a n WHERE NOT n.is_fleet)
SELECT participantId[:8] AS writer, count(*) AS notes,
  strftime(to_timestamp(min(createdAtMillis)/1000),'%Y-%m-%d') AS first_note,
  round(100*avg(sync_any_ai::INT),1) AS pct_with_other_ai_within_1min,
  round(100*avg(sync_fleet::INT),1) AS pct_with_fleet_within_1min
FROM x JOIN a USING (noteId, participantId) GROUP BY participantId ORDER BY notes DESC LIMIT 12""").show(max_rows=20)
print("== busiest pairs of non-fleet AI writers (same post, different writers)")
con.sql("""
SELECT x.participantId[:8] AS w1, y.participantId[:8] AS w2, count(*) AS pairs,
  round(100*avg((abs(x.createdAtMillis - y.createdAtMillis) < 60000)::INT),1) AS pct_within_1min,
  round(median(abs(x.createdAtMillis - y.createdAtMillis))/1000) AS median_gap_sec
FROM a x JOIN a y ON x.tweetId = y.tweetId AND x.participantId < y.participantId
WHERE NOT x.is_fleet AND NOT y.is_fleet GROUP BY ALL ORDER BY pairs DESC LIMIT 8""").show()
print("== AI-AI pairs under 1 minute, by who is in them")
con.sql("""
SELECT CASE WHEN x.is_fleet OR y.is_fleet THEN 'one side fleet' ELSE 'neither is fleet' END AS kind, count(*) AS pairs
FROM a x JOIN a y ON x.tweetId = y.tweetId AND x.participantId < y.participantId
 AND abs(x.createdAtMillis - y.createdAtMillis) < 60000 AND NOT (x.is_fleet AND y.is_fleet) GROUP BY 1""").show()
