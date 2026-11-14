"""Figures for the report and slides, from results/tables.

Fig 1: who writes the shown notes, by month (stacked bars, shares).
Fig 2: within-post vs cross-post text similarity (share of pairs above the human top-5% bar).
Palette: categorical slots 1-3 of the reference palette, validated (light, surface #fcfcfb);
slot 3 is below 3:1 contrast, so every series is also direct-labelled.
"""
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
T, F = ROOT / "results" / "tables", ROOT / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
SURF, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e6e5e1"
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
                     "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF})

def style(ax):
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8); ax.set_axisbelow(True)
    ax.tick_params(length=0)

# ---- Fig 1
rows = list(csv.DictReader(open(T / "extA_concentration_monthly.csv")))
months = [r["month"] for r in rows]
fleet = [float(r["fleet_pct_shown"]) for r in rows]
other = [float(r["other_ai_pct_shown"]) for r in rows]
human = [float(r["human_pct_shown"]) for r in rows]
labels = [("Sep\n2025" if m == "2025-09" else "Jan\n2026" if m == "2026-01" else
           {"03": "Mar", "05": "May", "07": "Jul", "09": "Sep", "11": "Nov"}.get(m[5:], "")) for m in months]
fig, ax = plt.subplots(figsize=(7.2, 3.9), dpi=200)
x = range(len(months)); w = 0.72
kw = dict(width=w, edgecolor=SURF, linewidth=1.2)
ax.bar(x, fleet, color=S1, label="Fleet (six AI accounts)", **kw)
ax.bar(x, other, bottom=fleet, color=S2, label="Other AI writers", **kw)
ax.bar(x, human, bottom=[a + b for a, b in zip(fleet, other)], color=S3, label="Human writers", **kw)
style(ax); ax.set_ylim(0, 100); ax.set_yticks([0, 25, 50, 75, 100]); ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
ax.set_xticks(list(x)); ax.set_xticklabels(labels)
last = len(months) - 1
for y, txt in ((fleet[last] / 2, "Fleet"), (fleet[last] + other[last] / 2, "Other AI"), (fleet[last] + other[last] + human[last] / 2, "Humans")):
    ax.text(last + 0.55, y, txt, va="center", ha="left", color=INK2, fontsize=9)
ax.set_xlim(-0.6, last + 1.6)
ax.set_title("Who writes the notes that readers see", loc="left", fontsize=12, color=INK, pad=22)
ax.text(0, 1.03, "Share of shown notes by month written. Apr to Nov 2026: fleet 51%. November partial.",
        transform=ax.transAxes, fontsize=8.5, color=INK2)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=3, frameon=False, fontsize=9, handlelength=1, handleheight=1)
fig.tight_layout(); fig.savefig(F / "fig1_who_writes_shown_notes.png"); plt.close(fig)

# ---- Fig 2
d = {r["group"]: r for r in csv.DictReader(open(T / "extD_cross_post.csv")) if r["measure"] == "text above human top-5%"}
main = {r["group"]: r for r in csv.DictReader(open(T / "step5_text_main.csv"))}   # same numbers and CI as the report
groups = [("Two human writers", "human-human"), ("Two AI writers,\ndifferent operators", "AI-AI")]
fig, ax = plt.subplots(figsize=(6.4, 3.6), dpi=200)
bw, gap = 0.34, 0.04
for i, (name, key) in enumerate(groups):
    wv = 100 * float(main[key]["share_above_human_top5pct"]); cv = 100 * float(d[key]["cross_post"])
    xw, xc = i - bw / 2 - gap / 2, i + bw / 2 + gap / 2
    ax.bar(xw, wv, bw, color=S1, edgecolor=SURF, linewidth=1.2, label="Same post" if i == 0 else None)
    top = wv
    if key == "AI-AI":
        lo, hi = 100 * float(main[key]["lo"]), 100 * float(main[key]["hi"])
        ax.errorbar(xw, wv, yerr=[[wv - lo], [hi - wv]], color=INK2, lw=1, capsize=3); top = hi
    ax.bar(xc, max(cv, 0.15), bw, color=S2, edgecolor=SURF, linewidth=1.2, label="Different posts, same day" if i == 0 else None)
    ax.text(xw, top + 0.4, f"{wv:.1f}%", ha="center", color=INK, fontsize=9.5)
    ax.text(xc, max(cv, 0.15) + 0.4, f"{cv:.1f}%", ha="center", color=INK, fontsize=9.5)
style(ax); ax.set_ylim(0, 16); ax.set_yticks([0, 5, 10, 15]); ax.set_yticklabels(["0%", "5%", "10%", "15%"])
ax.set_xticks([0, 1]); ax.set_xticklabels([g[0] for g in groups]); ax.set_xlim(-0.6, 1.6)
ax.set_title("AI notes sound alike only when they answer the same post", loc="left", fontsize=12, color=INK, pad=22)
ax.text(0, 1.03, "Pairs more alike in wording than the top 5% of human pairs. 95% CI.",
        transform=ax.transAxes, fontsize=8.5, color=INK2)
ax.legend(loc="upper left", frameon=False, fontsize=9, handlelength=1, handleheight=1)
fig.tight_layout(); fig.savefig(F / "fig2_same_post_vs_cross_post.png"); plt.close(fig)
print("ok")
