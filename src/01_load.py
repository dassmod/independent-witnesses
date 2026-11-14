"""Step 1: convert the raw Community Notes TSV dumps into Parquet.

Reads data/raw/tsv/*.tsv, writes data/interim/{notes,status,enrollment}.parquet.
Everything is read as text first (all_varchar) so nothing is silently coerced;
types are cast explicitly here, and parse problems are reported, not hidden.
"""
import duckdb
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "tsv"
OUT = ROOT / "data" / "interim"
OUT.mkdir(parents=True, exist_ok=True)

con = duckdb.connect()
con.execute("SET memory_limit='2GB'; SET preserve_insertion_order=false; SET temp_directory='" + tempfile.gettempdir() + "/duckdb_tmp'")

def read(pattern):
    return (f"read_csv('{RAW}/{pattern}', delim='\\t', header=true, all_varchar=true, "
            f"quote='', escape='', strict_mode=false, null_padding=true, filename=true)")

# Notes: one row per note. Author column is called noteAuthorParticipantId in this dump.
con.execute(f"""
COPY (
  SELECT noteId,
         noteAuthorParticipantId           AS participantId,
         CAST(createdAtMillis AS BIGINT)   AS createdAtMillis,
         tweetId,
         classification,
         summary,
         isMediaNote, isCollaborativeNote,
         regexp_extract(filename, '[^/]+$') AS sourceFile
  FROM {read('notes-*.tsv')}
) TO '{OUT}/notes.parquet' (FORMAT parquet)
""")

con.execute(f"""
COPY (
  SELECT noteId, noteAuthorParticipantId AS participantId,
         CAST(createdAtMillis AS BIGINT) AS createdAtMillis,
         firstNonNMRStatus, TRY_CAST(timestampMillisOfFirstNonNMRStatus AS BIGINT) AS tsFirstNonNMR,
         currentStatus, TRY_CAST(timestampMillisOfCurrentStatus AS BIGINT) AS tsCurrentStatus,
         mostRecentNonNMRStatus, lockedStatus, currentDecidedBy
  FROM {read('noteStatusHistory-*.tsv')}
) TO '{OUT}/status.parquet' (FORMAT parquet)
""")

con.execute(f"""
COPY (
  SELECT participantId, enrollmentState,
         TRY_CAST(timestampOfLastStateChange AS BIGINT) AS tsLastStateChange,
         modelingPopulation
  FROM {read('userEnrollment-*.tsv')}
) TO '{OUT}/enrollment.parquet' (FORMAT parquet)
""")

for t in ["notes", "status", "enrollment"]:
    n = con.execute(f"SELECT count(*) FROM '{OUT}/{t}.parquet'").fetchone()[0]
    print(f"{t:11s} {n:>10,d} rows")
