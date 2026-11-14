"""Steps 2-3 prep: build the analysis sample following docs/decisions.md.

Sample: non-collaborative MISLEADING notes since the first AI note, on posts
that have notes from at least two different participants. For each note:
normalized source URLs (with the exclusions from decisions.md) and language.
Writes data/interim/sample.parquet.
"""
import duckdb, tempfile, re, html, json, time
from pathlib import Path
from urllib.parse import parse_qs
import py3langid as langid

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "interim"
MISLEADING = "MISINFORMED_OR_POTENTIALLY_MISLEADING"
FLEET_MIN_NOTES = 50_000   # AI writers above this many notes in the window = the fleet (one author)

con = duckdb.connect()
con.execute("SET memory_limit='2GB'; SET temp_directory='" + tempfile.gettempdir() + "/duckdb_tmp'")
con.execute(f"""
CREATE TABLE base AS
SELECT n.noteId, n.participantId, n.tweetId, n.createdAtMillis, n.classification, n.summary,
       starts_with(e.enrollmentState,'api') AS is_ai
FROM '{D}/notes.parquet' n JOIN '{D}/enrollment.parquet' e USING (participantId)
WHERE n.isCollaborativeNote='0'
  AND n.createdAtMillis >= (SELECT min(createdAtMillis) FROM '{D}/notes.parquet' x
                            JOIN '{D}/enrollment.parquet' f USING (participantId)
                            WHERE starts_with(f.enrollmentState,'api'))""")
con.execute(f"CREATE TABLE fleet AS SELECT participantId FROM base WHERE is_ai GROUP BY 1 HAVING count(*) > {FLEET_MIN_NOTES}")
print("fleet writers:", con.execute("SELECT count(*) FROM fleet").fetchone()[0], flush=True)
con.execute(f"""
CREATE TABLE s AS
SELECT b.*, b.participantId IN (SELECT participantId FROM fleet) AS is_fleet
FROM base b
WHERE b.classification='{MISLEADING}'
  AND b.tweetId IN (SELECT tweetId FROM base WHERE classification='{MISLEADING}'
                    GROUP BY 1 HAVING count(DISTINCT participantId) >= 2)""")
print("sample notes:", con.execute("SELECT count(*) FROM s").fetchone()[0], flush=True)

URL_RE = re.compile(r'https?://[^\s<>"]+', re.I)
TRAIL = ".,;:)]}'\"!?"

def norm(u, tweet_id):
    u = html.unescape(u).rstrip(TRAIL)
    m = re.match(r'https?://([^/?#]+)([^?#]*)(\?[^#]*)?', u, re.I)
    if not m:
        return None
    host = re.sub(r'^(www\.|m\.|mobile\.)', '', m.group(1).lower())
    path = m.group(2).rstrip('/' + TRAIL)
    query = m.group(3) or ''
    if host == 'twitter.com':
        host = 'x.com'
    # exclusions from decisions.md
    if host == 'share.google' or host == 'help.x.com':
        return None
    if host == 'google.com' and path.startswith('/search'):
        return None
    if host == 'x.com' and path.startswith('/en/tos'):
        return None
    if tweet_id in u:   # any link that contains the noted post's own id (x.com/status/ID, opennotenetwork.com/posts/x--ID, ...)
        return None
    # YouTube: keep the video id, the only identifying query parameter
    if host == 'youtu.be':
        vid = path.strip('/').split('/')[0]
        return 'youtube.com/watch?v=' + vid if vid else None
    if host == 'youtube.com' and path == '/watch':
        v = parse_qs(query.lstrip('?')).get('v', [''])[0]
        return 'youtube.com/watch?v=' + v if v else None
    return host + path

out = D / "sample_extra.jsonl"
t0, done = time.time(), 0
cur = con.execute("SELECT noteId, tweetId, summary FROM s")
with open(out, "w") as f:
    while True:
        rows = cur.fetchmany(50_000)
        if not rows:
            break
        for note_id, tweet_id, summary in rows:
            summary = summary or ""
            urls = sorted({k for k in (norm(u, tweet_id) for u in URL_RE.findall(summary)) if k})
            text = re.sub(r'\s+', ' ', URL_RE.sub(' ', html.unescape(summary))).strip().lower()
            lang = langid.classify(text)[0] if text else 'und'
            f.write(json.dumps({"noteId": note_id, "urls": urls, "lang": lang, "text": text}) + "\n")
        done += len(rows)
        print(f"{done:,} notes, {time.time()-t0:.0f}s", flush=True)

con.execute(f"""
COPY (
  SELECT s.noteId, s.participantId, s.tweetId, s.createdAtMillis, s.is_ai, s.is_fleet,
         e.urls, e.lang, e.text
  FROM s JOIN read_json('{out}', columns={{noteId:'VARCHAR', urls:'VARCHAR[]', lang:'VARCHAR', text:'VARCHAR'}}) e
  USING (noteId)
) TO '{D}/sample.parquet' (FORMAT parquet)""")
print("done", flush=True)
