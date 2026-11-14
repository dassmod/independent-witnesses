"""Step 1 check: what the data looks like before any design decision.

Writes results/tables/step1_*.csv. Window starts 2025-09-02, the first note by an
AI writer (enrollmentState starting with 'api'). Collaborative notes are excluded.
"""
import duckdb
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "interim"
T = ROOT / "results" / "tables"
T.mkdir(parents=True, exist_ok=True)

con = duckdb.connect()
con.execute("SET memory_limit='2GB'; SET temp_directory='" + tempfile.gettempdir() + "/duckdb_tmp'")
con.execute(f"""
CREATE TABLE n AS
SELECT noteId, participantId, tweetId, createdAtMillis, summary,
       starts_with(e.enrollmentState, 'api') AS is_ai
FROM '{D}/notes.parquet' JOIN '{D}/enrollment.parquet' e USING (participantId)
WHERE isCollaborativeNote = '0'
  AND createdAtMillis >= (SELECT min(createdAtMillis) FROM '{D}/notes.parquet'
                          JOIN '{D}/enrollment.parquet' e USING (participantId)
                          WHERE starts_with(e.enrollmentState, 'api'))
""")

queries = {
    "monthly_share": """
        SELECT strftime(to_timestamp(createdAtMillis/1000), '%Y-%m') AS month,
               count(*) FILTER (WHERE is_ai) AS ai_notes,
               count(*) FILTER (WHERE NOT is_ai) AS human_notes,
               count(DISTINCT participantId) FILTER (WHERE is_ai) AS ai_writers
        FROM n GROUP BY 1 ORDER BY 1""",
    "ai_writers": """
        SELECT participantId, count(*) AS notes,
               min(to_timestamp(createdAtMillis/1000))::DATE AS first_note,
               max(to_timestamp(createdAtMillis/1000))::DATE AS last_note
        FROM n WHERE is_ai GROUP BY 1 ORDER BY notes DESC""",
    "notes_per_post": """
        SELECT k AS notes_on_post, count(*) AS posts
        FROM (SELECT tweetId, count(*) AS k FROM n GROUP BY 1) GROUP BY 1 ORDER BY 1""",
    "pair_groups": """
        SELECT CASE WHEN a.is_ai AND b.is_ai THEN 'AI-AI'
                    WHEN a.is_ai OR b.is_ai THEN 'AI-human' ELSE 'human-human' END AS grp,
               count(*) AS pairs, count(DISTINCT a.tweetId) AS posts,
               median(abs(a.createdAtMillis - b.createdAtMillis)) / 3.6e6 AS median_gap_hours
        FROM n a JOIN n b ON a.tweetId = b.tweetId AND a.noteId < b.noteId
                          AND a.participantId <> b.participantId
        GROUP BY 1 ORDER BY 1""",
    "links": r"""
        SELECT is_ai, count(*) AS notes,
               avg((summary LIKE '%http%')::INT) AS share_with_link,
               avg((summary LIKE '%t.co/%')::INT) AS share_tco,
               avg(len(regexp_extract_all(summary, 'https?://\S+'))) AS links_per_note,
               median(len(summary)) AS median_chars
        FROM n GROUP BY 1""",
}
for name, sql in queries.items():
    con.execute(f"COPY ({sql}) TO '{T}/step1_{name}.csv' (HEADER)")
    print(f"\n== {name}"); con.sql(sql).show(max_rows=20)
