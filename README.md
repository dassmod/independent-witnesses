# Independent Witnesses

On the same X post, are two Community Notes written by AI writers more alike (shared sources, similar text) than two notes written by humans?

Apart Research, AI x Epistemics Research Sprint, 13 to 15 November 2026. Track 2 (trust infrastructure) with a Track 4 angle.

## Data

Community Notes public data, downloaded 14 Nov 2026 from x.com/i/communitynotes/download-data (dump dated 12 Nov 2026). Files used: Notes (`notes-0000[0-4]`), Note Status History, User Enrollment. Not redistributed here; put the zips in `data/raw/`.

AI writers are participants whose `enrollmentState` starts with `api`. See `docs/data-notes.md` for what the data actually looks like.

## Reproduce

```bash
pip install -r requirements.txt
mkdir -p data/raw/tsv && for f in data/raw/*.zip; do unzip -o -q "$f" -d data/raw/tsv; done
python src/01_load.py      # TSV -> data/interim/*.parquet
python src/02_inspect.py   # step 1 counts -> results/tables/step1_*.csv
```

## Layout

```
src/          numbered pipeline scripts
results/      tables/ and figures/ produced by src/
docs/         data notes, method decisions
report/       the Apart report
data/         local only (gitignored)
```

## Prior work

Conceptual link to swarm-canaries (github.com/dassmod/swarm-canaries, Apart Swarm Alignment sprint, Nov 2026): agreement between correlated models can look like independent confirmation. No code reused. All code here written during the sprint.
