"""Extension A: who writes the notes that are shown.

Non-collaborative MISLEADING notes since the first AI note. Shown = currentStatus
CURRENTLY_RATED_HELPFUL. By creation month: share of submitted and of shown notes written by
the fleet (six AI writers with > 50,000 notes), other AI writers, and humans.
Recent months are not settled: most of their notes still need ratings.
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
  SELECT n.noteId, n.participantId, n.createdAtMillis, n.classification, starts_with(e.enrollmentState, 'api') AS is_ai
  FROM '{D}/notes.parquet' n JOIN '{D}/enrollment.parquet' e USING (participantId)
  WHERE n.isCollaborativeNote = '0'
    AND n.createdAtMillis >= (SELECT min(createdAtMillis) FROM '{D}/notes.parquet' x
                              JOIN '{D}/enrollment.parquet' f USING (participantId) WHERE starts_with(f.enrollmentState, 'api'))),
fleet AS (SELECT participantId FROM base WHERE is_ai GROUP BY 1 HAVING count(*) > 50000)
SELECT b.*, b.participantId IN (SELECT participantId FROM fleet) AS is_fleet,
       s.currentStatus = 'CURRENTLY_RATED_HELPFUL' AS shown,
       s.currentStatus = 'NEEDS_MORE_RATINGS' AS nmr,
       strftime(to_timestamp(b.createdAtMillis / 1000), '%Y-%m') AS month
FROM base b JOIN '{D}/status.parquet' s USING (noteId)
WHERE b.classification = 'MISINFORMED_OR_POTENTIALLY_MISLEADING'""")
sql = """
SELECT month, count(*) AS submitted, sum(shown::INT) AS shown,
  round(100 * avg(nmr::INT), 1) AS pct_still_need_ratings,
  round(100 * avg(is_fleet::INT), 1) AS fleet_pct_submitted,
  round(100 * avg((is_ai AND NOT is_fleet)::INT), 1) AS other_ai_pct_submitted,
  round(100 * sum((shown AND is_fleet)::INT) / sum(shown::INT), 1) AS fleet_pct_shown,
  round(100 * sum((shown AND is_ai AND NOT is_fleet)::INT) / sum(shown::INT), 1) AS other_ai_pct_shown,
  round(100 * sum((shown AND NOT is_ai)::INT) / sum(shown::INT), 1) AS human_pct_shown
FROM a GROUP BY 1 ORDER BY 1"""
con.execute(f"COPY ({sql}) TO '{T}/extA_concentration_monthly.csv' (HEADER)")
con.sql(sql).show(max_rows=20)
tot = """SELECT 'Apr-Nov 2026' AS period, sum(shown::INT) AS shown,
  round(100 * sum((shown AND is_fleet)::INT) / sum(shown::INT), 1) AS fleet_pct_shown,
  round(100 * sum((shown AND is_ai)::INT) / sum(shown::INT), 1) AS all_ai_pct_shown,
  round(100 * avg(is_fleet::INT), 1) AS fleet_pct_submitted
FROM a WHERE month >= '2026-04'"""
con.execute(f"COPY ({tot}) TO '{T}/extA_concentration_total.csv' (HEADER)")
con.sql(tot).show()
