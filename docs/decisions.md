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

(empty)
