# Slide outline (PDF deck, also the script for a 3 to 5 minute video)

Draft structure. Nine slides, about 30 seconds each. Every slide title is the claim of that slide. One figure or one table per slide, no paragraphs.

| # | Title (the claim) | On the slide | Say (one or two sentences) | Source |
|---|---|---|---|---|
| 1 | Two notes, one witness | The Bollywood pair side by side: two accounts, same minute, same two links in opposite order | These look like two contributors agreeing. They are two accounts of one system. | reading file, example pair |
| 2 | Community Notes checks that raters are independent. Nobody checks the writers | Small diagram: writers propose, raters decide, bridging sits on the rater side. One line: AI writers now submit more than half of new notes | Agreement is evidence only if witnesses are independent. The design tests that for raters only. | Wojcik 2022; Gong and Wu 2026 |
| 3 | Six accounts behave as one system | Three facts: 86% of AI notes; five started on 17 Dec 2025; 1, 2 or 3 of them per post, never more | We call them the fleet and count them as one author. | `docs/data-notes.md` |
| 4 | That system writes half of what readers see | Figure 1: monthly share of shown notes (fleet, other AI, human). Callouts: 51% Apr to Nov 2026; on 34% of covered posts nobody else wrote | Not an accusation, the notes are rated helpful. It is a dependence with no signal attached. | `extA_`, `extE_` tables |
| 5 | The question and three things that fake the answer | Question in one line. Three controls: fleet as one author, same time window, every post weighs the same. Footer: rules and refutation committed before results | Human pairs on the same post are the baseline. | `docs/decisions.md` |
| 6 | Different operators mostly use different sources | Two bars: Jaccard 0.171 vs 0.156, difference +0.015 [0.010, 0.020]. Small note: "at least one shared link" 40% vs 21% overstates, AI notes carry more links | The preregistered result is real and small. | `step4_main.csv` |
| 7 | Given the same post, they write the same words | Figure 2: share above the human top-5% bar: human 5%, AI-human 6%, AI-AI 12.1%, fleet 16.9%. Beside it: cross-post pairs 0.0%; near copies 0.05% | Not copying and not house style. It appears only on the same post. | `step5_`, `extD_`, `step8_` tables |
| 8 | Two predictions failed | Shared fate: +0.049 [-0.015, +0.111]. Trend: no rise. Robustness table in small print | We found concentration and resemblance, not harm to outcomes. | `extB_`, `extC_`, `extF_` tables |
| 9 | What to do, and what comes next | Three asks: an operator field for AI writers; concentration and similarity as a standing metric; treat near-duplicate notes as one when routing raters. Next: the Ratings file. Repo link | On the writing side the crowd has become mostly one voice, and nothing in the system says so. | report section 5 |

## Notes

- Figures 1 and 2 do not exist yet. Both come straight from the tables named above.
- Slide 1 shows note text. It is public data, but keep it to this one pair and do not show participant ids.
- Limits go on slide 8 or 9 in one line: behaviour, not proof of one operator; no post text; small reading sample.
- For the PDF: export at 16:9, large type, the claim readable without the voice.
