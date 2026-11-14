"""Step 8: compare Das's reading labels with Gemini's, check both against what the URL lists say,
then open the key and show the labels by group.

Das answered with option numbers: Q1 same evidence 1=yes 2=partly 3=no; Q2 shared source
1=obvious 2=choice 3=none shared; Q3 subset 1=A in B 2=B in A 3=no ("1 2" = identical lists).
"""
import csv, json, re
from collections import Counter
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results" / "reading"
Q1 = {"1": "yes", "2": "partly", "3": "no"}
Q2 = {"1": "obvious", "2": "choice", "3": "none_shared"}

das = {}
s = (R / "pairs_to_read.md").read_text()
for m in re.finditer(r'## Pair (\d+)\n.*?\*\*Мои ответы:\*\*\n(.*?)(?=\n---|\Z)', s, re.S):
    a = [l.split(':', 1)[1].strip() if ':' in l else '' for l in m.group(2).strip().split('\n')]
    if a[0]:
        q3 = set(re.findall(r'[123]', a[2]))
        das[int(m.group(1))] = {"same_evidence": Q1[a[0]], "source_choice": Q2[a[1]],
                                "subset": "identical" if q3 == {"1", "2"} else {"1": "A_in_B", "2": "B_in_A", "3": "no"}[q3.pop()]}
gem = {}
for line in (R / "gemini_labels.jsonl").read_text().splitlines():
    if line.strip():
        d = json.loads(line); gem[d["pair"]] = d

key = {int(r["pair"]): r for r in csv.DictReader(open(R / "key.csv"))}
con = duckdb.connect()
urls = dict(con.execute(f"SELECT noteId, urls FROM '{ROOT}/data/interim/sample.parquet'").fetchall())
truth = {}
for p, r in key.items():
    A, B = set(urls[r["noteA"]]), set(urls[r["noteB"]])
    truth[p] = {"shared": bool(A & B),
                "subset": "identical" if A == B else "A_in_B" if A < B else "B_in_A" if B < A else "no"}

def subset_ok(label, t):   # Gemini was told to write A_in_B for identical lists
    return label == t or (t == "identical" and label in ("A_in_B", "identical"))

print(f"Das labeled {len(das)} pairs, Gemini {len(gem)} pairs, Gemini opened links: {sum(g['opened_links'] for g in gem.values())}\n")
print("== checks against the URL lists (objective)")
for who, lab in (("Das", das), ("Gemini", gem)):
    ps = sorted(lab)
    ok_sub = sum(subset_ok(lab[p]["subset"], truth[p]["subset"]) for p in ps)
    ok_shared = sum((lab[p]["source_choice"] != "none_shared") == truth[p]["shared"] for p in ps)
    print(f"  {who:6s} subset correct {ok_sub}/{len(ps)}   'any shared link' correct {ok_shared}/{len(ps)}")
print("\n== agreement Das vs Gemini on the pairs Das labeled")
both = sorted(set(das) & set(gem))
for f in ("same_evidence", "source_choice"):
    agree = [p for p in both if das[p][f] == gem[p][f]]
    print(f"  {f:14s} {len(agree)}/{len(both)}   disagree on pairs: {[ (p, das[p][f], gem[p][f]) for p in both if p not in agree]}")

print("\n== KEY OPENED: labels by group")
for who, lab in (("Das", das), ("Gemini", gem)):
    for grp in ("AI-AI", "human-human"):
        for kind in ("high", "none"):
            ps = [p for p in lab if key[p]["group"] == grp and key[p]["sampled_as"] == kind]
            if ps:
                print(f"  {who:6s} {grp:11s} sampled {kind:4s} n={len(ps):2d}  same_evidence {dict(Counter(lab[p]['same_evidence'] for p in ps))}  source {dict(Counter(lab[p]['source_choice'] for p in ps))}")
with open(R / "reading_merged.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["pair", "group", "sampled_as", "jaccard", "gap_min", "truth_subset", "das_same", "das_source", "das_subset", "gem_same", "gem_source", "gem_subset", "gem_note"])
    for p in sorted(key):
        d, g = das.get(p, {}), gem.get(p, {})
        w.writerow([p, key[p]["group"], key[p]["sampled_as"], key[p]["jaccard"], key[p]["gap_min"], truth[p]["subset"],
                    d.get("same_evidence", ""), d.get("source_choice", ""), d.get("subset", ""),
                    g.get("same_evidence", ""), g.get("source_choice", ""), g.get("subset", ""), g.get("note", "")])
