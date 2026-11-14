# Method decisions

Written 14 Nov 2026, before any similarity between notes was computed. Decisions marked **(Das)** were made by Das; the rest are technical choices proposed by Claude and accepted by Das. Changing anything here after results are seen must be logged at the bottom with the reason.

## Question

On the same post, do two notes by AI writers of different operators share sources more than two notes by human writers?

## Sample

- Window: notes created from 2 Sep 2025 (first AI note) to the end of the dump (12 Nov 2026).
- Collaborative notes excluded.
- **(Das)** Only notes classified `MISINFORMED_OR_POTENTIALLY_MISLEADING`. These are the notes that can be shown under a post; "no note needed" notes are a different genre.
- AI writer: `enrollmentState` starts with `api` (current snapshot).
- Pairs: two notes on the same `tweetId` by different authors. Groups: AI-AI, human-human (AI-human kept for context).
- **(Das)** The six high-volume AI writers (each over 50,000 notes in the window; five started 17 Dec 2025, posts dealt out at most two or three per post) are treated as **one author**. Pairs inside the fleet are therefore not AI-AI pairs in the main result. They are reported on a separate line as an illustration of how the system counts voices.
- Both notes in the same language (py3langid on the note text with links removed).

## Main measure: shared sources **(Das: sources are the main result, text is secondary)**

- Links extracted from `summary`.
- Normalization: lowercase host; drop `http(s)://`, leading `www.`, `m.`, `mobile.`; decode `&amp;`; drop fragments (`#...`, including `#:~:text=`); drop trailing `/` and trailing punctuation; drop query strings except identifying parameters (YouTube `v`); `youtu.be/ID` maps to `youtube.com/watch?v=ID`; drop tracking parameters (`utm_*`).
- Excluded before comparison: `google.com/search` links, `share.google` short links (cannot be expanded offline), links to the noted post itself, X policy pages (`help.x.com`, `x.com/en/tos`). Other x.com links are kept: another post can be a real source.
- Unit: the normalized URL (one document). Domain-level overlap reported as a secondary line.
- Per pair: Jaccard of the two URL sets (shared / union). Secondary: at least one shared URL.
- Only pairs where both notes keep at least one link after exclusion.

## Secondary measure: text

- Links removed, lowercased, whitespace collapsed.
- Character 4-gram sets, Jaccard per pair.
- Headline: share of AI-AI pairs above the threshold set by the most similar 5% of human-human pairs (post-weighted, per time window). Under human-like independence this is about 5%. Mean similarity reported alongside.
- Embedding cosine (multilingual model) only if time allows, as a check.

## Controls

- **(Das)** Time gap: compare only within the same window: under 1 hour, 1 to 6 hours, 6 to 24 hours. Pairs more than 24 hours apart are dropped from the comparison (almost no AI-AI pairs there). A single overall number reweights human-human windows to the AI-AI time profile.
- The under-1-minute pairs are reported separately: the second writer cannot have read the first note, so similarity there is not copying.
- **(Das)** Each post weighs the same: a pair gets weight 1 / (number of pairs of its group on that post).
- Robustness: posts that have both an AI-AI and a human-human pair.
- Not possible from the data: the plan's control "source matches the link in the post itself", because post content is not in the dump. Named as a limitation.

## Uncertainty

Cluster bootstrap over posts (resample posts, keep all their pairs), 1,000 resamples, 95% intervals. Every number reported with its count of pairs and posts.

## What proves the hypothesis wrong

The post-weighted, time-matched difference in source Jaccard between AI-AI pairs (different operators) and human-human pairs has a 95% interval that includes zero or lies below it. That is reported as the result: AI writers of different operators are as independent in their sources as humans.

## Change log

- 14 Nov 2026, before any pair was computed: the exclusion "links to the noted post itself" is applied to any URL that contains the post's own id, not only x.com/status links. Reason: 169 AI notes link the post through opennotenetwork.com/posts/x--ID.

- 14 Nov 2026, after the first main number was seen (Jaccard difference +0.015, 95% CI [+0.010, +0.020]); these are post hoc and marked as such:
  - Robustness check added: pairs in English only. Result: difference +0.019 [+0.014, +0.024]. Language mix does not explain the gap.
  - Check of who the AI writers outside the fleet are. Six writers (6531ED68, 9A4E061C, C08CB980, A09F8A99, 46EF8576, EA7F9E35) post within about one second of each other; they account for 98% of non-fleet AI-AI pairs under one minute. Start dates differ (Sep 2025 to Feb 2026), volumes are small. Same operator or a shared trigger (all respond to the same note requests) cannot be told apart from this data.
  - **(Das)** Decision: these six are NOT merged into one author. The main result stays as defined above. Planned instead: a robustness row without pairs under one minute.
  - The under-1-minute AI-AI line (0.285 vs 0.205 human) is dominated by these six writers and is not used as separate evidence.

- 14 Nov 2026, more post hoc robustness and the secondary measure (computed after the main number was seen; method unchanged):
  - Without pairs under one minute: Jaccard difference +0.011 [+0.006, +0.015].
  - Text measure (4-gram Jaccard, threshold from the top 5% of human-human pairs per window): AI-AI pairs above threshold 12.1% pooled [10.8, 13.6]; AI-human 6.0%; fleet-fleet 16.9%. Mean text similarity of AI-AI pairs stays about 0.20 across time windows, human-human falls from 0.118 to 0.093.
  - Text measure uses all same-language pairs with at least 4 characters of text; links are not required (they are for the source measure).
  - Reading file for step 8 is built blind (group hidden, key kept separately, gitignored) from the source-measure pair set, gap up to 6 hours.

- 14 Nov 2026, step 8 (reading) and copies, post hoc:
  - Das read 27 of the 40 blind pairs; Gemini labeled all 40 with the same three questions and did not open links (judged from URLs and text). Agreement on "same evidence": 17/27. The "obvious vs choice" label is unreliable (systematic disagreement) and is used only descriptively. In high-overlap pairs, human pairs rest on the same evidence more often (Das 7/9, Gemini 14/15) than AI pairs (Das 5/11, Gemini 10/15): AI pairs with a shared link more often share only part of the evidence, which is why "any shared link" overstates dependence and Jaccard is kept as the main measure.
  - Copies (src/09): near copies (4-gram Jaccard >= 0.8) are 1.16% of human-human pairs, 0.77% of AI-human, 0.05% of AI-AI (post-weighted). AI-AI similarity is not copying; copying sits in the human baseline and is too rare to explain the text gap.

# Extension, registered 15 Nov 2026 before computing B and C **(Das: go ahead with A, B, C)**

Prompted by Gong and Wu (2026), who name "studies of writer diversity and governance" as future work, and by a quick check of who writes the shown notes (seen before this entry, see A).

## A. Concentration of shown notes (descriptive)

- Notes: non-collaborative, MISLEADING, created since 2 Sep 2025. Shown = `currentStatus` CURRENTLY_RATED_HELPFUL.
- By creation month: share of shown notes and of submitted notes written by the fleet, other AI writers, humans.
- Already seen before this entry: fleet share of shown notes 48.0% (2026 Q2), 51.9% (Q3), 56.3% (Q4 to 12 Nov). Reported as descriptive, with the caveat that recent months are not settled (most notes still need ratings).

## B. Shared fate of two notes on the same post

- Pairs: same rules as the main measure (same post, different authors, same language, gap up to 24 hours, MISLEADING, fleet as one author with fleet-fleet as its own group). No link requirement.
- Only pairs where both notes have a decided `currentStatus` (CURRENTLY_RATED_HELPFUL = 1, CURRENTLY_RATED_NOT_HELPFUL = 0).
- Measure: phi correlation of the two outcomes, from the post-weighted 2x2 table. Human-human windows reweighted to the AI-AI time profile (<1h, 1-6h, 6-24h), as in the main measure. Cluster bootstrap over posts, 1,000 resamples.
- What proves it wrong: the 95% interval of phi(AI-AI) minus phi(human-human) includes zero or lies below it. Then AI notes on one post do not share fate more than human notes do.
- Secondary: within AI-AI pairs, concordance (same outcome) for pairs above vs below the human top-5% text threshold, and for pairs with vs without a shared source.
- Known limits, written now: few AI notes are rated not helpful, so the interval may be wide; status depends on raters, who often rate both notes on a post (true for both groups).

## C. AI-AI similarity over time

- Same pairs and measures as the main source measure and the text measure, grouped by the creation month of the later note.
- Expectation from the shared-template mechanism: AI-AI similarity rises as more writers join.
- What proves it wrong: source Jaccard and the text above-threshold share of AI-AI pairs in Jul-Nov 2026 are not higher than in Nov 2025-Mar 2026 (95% interval of the difference includes zero or lies below it).

## Results of the extension (15 Nov 2026)

- A: Apr-Nov 2026, the fleet wrote 51.2% of shown MISLEADING notes (43.5% of submitted); all AI writers 56.5% of shown. Monthly table in results/tables/extA_concentration_monthly.csv.
- B: phi AI-AI 0.843 [0.785, 0.898], human-human 0.794 [0.766, 0.818], difference +0.049 [-0.015, +0.111]. **Refuted by the registered criterion**: AI notes on one post do not share fate measurably more than human notes. Fate is strongly shared in every group (the post and its raters dominate). AI-human pairs share fate less (0.527). Not-helpful AI notes are rare (AI-AI decided pairs: 95.6% helpful), so the test has little room.
- C: AI-AI late minus early: source Jaccard +0.005 [-0.003, +0.013], text above threshold -0.009 [-0.019, +0.002]. **Refuted by the registered criterion**: AI-AI similarity did not rise as writers joined; it is about stable from late 2025 on.

# Second extension, registered 15 Nov 2026 before computing **(Das: go ahead with 1, 4, 2)**

## D. Cross-post baseline: style versus shared content

- Within-post pairs: as in the main measure and the text measure.
- Cross-post pairs: notes in the same group, same language, created on the same calendar day (UTC), on different posts, by different authors (fleet counted as one author, so no fleet-fleet pairs). Built by shuffling notes inside each (day, language, group) bucket with a fixed seed and pairing neighbours. Their similarity measures shared style and shared news of the day, not a shared post.
- Measures: text above the human top-5% threshold (window of the pair's gap), mean 4-gram Jaccard, source Jaccard (both notes with links).
- Excess = within-post minus cross-post, for AI-AI and for human-human, pooled over the windows with the AI-AI within-post time profile.
- What proves the shared-content reading wrong: the 95% interval of (AI-AI excess minus human-human excess) for the text above-threshold share includes zero or lies below it. Then the AI text gap is style, not more shared content per post.
- Bootstrap: within-post pairs resampled by post, cross-post pairs by pair, 500 resamples each.

## E. Dependence of coverage on one system (descriptive)

- Posts with at least one shown note (CURRENTLY_RATED_HELPFUL, MISLEADING, created since 2 Sep 2025), all notes counted, collaborative notes (Grok drafts) included as their own source.
- Share of covered posts whose shown notes all come from the fleet; and of those, the share where no one else wrote any note. By month of the first shown note.

## F. Robustness of the headline numbers (descriptive)

Recompute the main source Jaccard difference and the AI-AI text above-threshold share under: fleet = top six (main), top seven (adds the next largest AI writer), no fleet merge; 3-gram instead of 4-gram; threshold at the human top 10% instead of 5%; windows <30 min, 30 min to 3 h, 3 to 24 h. Bootstrap over posts, 300 resamples. Reported whatever they show.
