"""Extension E: how much of the coverage rests on one system?

Registered in docs/decisions.md (15 Nov). Posts with at least one shown note (CURRENTLY_RATED_HELPFUL,
MISLEADING, created since the first AI note). All notes counted; collaborative notes (Grok drafts)
are their own source. Per post: who wrote the shown notes; whether anyone else wrote any note.
"""
import tempfile
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
D, T = ROOT / "data" / "interim", ROOT / "results" / "tables"
con = duckdb.connect()
con.execute("SET memory_limit='2GB'; SET temp_directory='" + tempfile.gettempdir() + "/duckdb_tmp'")
con.execute(f"""
CREATE TABLE a AS
WITH base AS (
  SELECT n.noteId, n.participantId, n.tweetId, n.createdAtMillis, n.classification, n.isCollaborativeNote,
         starts_with(e.enrollmentState, 'api') AS is_ai
  FROM '{D}/notes.parquet' n JOIN '{D}/enrollment.parquet' e USING (participantId)
  WHERE n.createdAtMillis >= (SELECT min(createdAtMillis) FROM '{D}/notes.parquet' x
                              JOIN '{D}/enrollment.parquet' f USING (participantId) WHERE starts_with(f.enrollmentState, 'api'))),
fleet AS (SELECT participantId FROM base WHERE is_ai AND isCollaborativeNote = '0' GROUP BY 1 HAVING count(*) > 50000)
SELECT b.*, CASE WHEN b.isCollaborativeNote = '1' THEN 'collab'
                 WHEN b.participantId IN (SELECT participantId FROM fleet) THEN 'fleet'
                 WHEN b.is_ai THEN 'ai_other' ELSE 'human' END AS src,
       s.currentStatus = 'CURRENTLY_RATED_HELPFUL' AND b.classification = 'MISINFORMED_OR_POTENTIALLY_MISLEADING' AS shown
FROM base b JOIN '{D}/status.parquet' s USING (noteId)""")
con.execute("""
CREATE TABLE p AS
SELECT tweetId,
  strftime(to_timestamp(min(createdAtMillis) FILTER (WHERE shown) / 1000), '%Y-%m') AS month,
  list_distinct(list(src) FILTER (WHERE shown)) AS shown_src,
  list_distinct(list(src)) AS all_src
FROM a GROUP BY 1 HAVING sum(shown::INT) > 0""")
sql = """
SELECT month, count(*) AS covered_posts,
  round(100 * avg((shown_src = ['fleet'])::INT), 1) AS pct_shown_only_fleet,
  round(100 * avg((all_src = ['fleet'])::INT), 1) AS pct_nobody_else_wrote,
  round(100 * avg((list_contains(shown_src, 'fleet'))::INT), 1) AS pct_any_fleet_shown,
  round(100 * avg((shown_src = ['human'])::INT), 1) AS pct_shown_only_human,
  round(100 * avg((shown_src = ['collab'])::INT), 1) AS pct_shown_only_collab
FROM p GROUP BY 1 ORDER BY 1"""
con.execute(f"COPY ({sql}) TO '{T}/extE_coverage_monthly.csv' (HEADER)")
con.sql(sql).show(max_rows=20)
tot = sql.replace("SELECT month,", "SELECT 'Apr-Nov 2026' AS period,").replace("FROM p GROUP BY 1 ORDER BY 1", "FROM p WHERE month >= '2026-04'")
con.execute(f"COPY ({tot}) TO '{T}/extE_coverage_total.csv' (HEADER)")
con.sql(tot).show()
