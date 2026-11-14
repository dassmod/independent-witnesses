<!-- DRAFT written by Claude from the results in results/tables and docs/decisions.md.
     Das: rewrite in your own words before it goes into the official Apart template.
     Limit: 8 pages without references and appendices. Marked TODO items are yours. -->

# Two Notes, One Witness: Concentration and Resemblance among AI Note Writers on Community Notes

Dastan Modubash, independent. With Apart Research.
<!-- TODO title is a proposal; the same title replaces earlier submissions. -->

## Abstract

Community Notes shows a fact-checking note only when raters who usually disagree both find it helpful. That design tests the independence of raters. It does not test the independence of writers, and since September 2025 writers include AI systems that now submit more than half of new notes. Using X's public data up to 12 November 2026, we ask whether two AI-written notes on the same post are more alike than two human-written notes, with human pairs matched on time gap and every post weighted equally. Methods and refutation criteria were committed before results. Three findings. First, six AI accounts behave as one system and wrote 51% of all notes shown to readers from April to November 2026; on 34% of covered posts nobody else wrote a note. Second, AI writers from different operators share sources only slightly more than humans (Jaccard difference +0.015, 95% CI [+0.010, +0.020]). Third, their wording is far more alike: 12.1% of AI pairs exceed the similarity that only 5% of human pairs reach. This is neither copying nor house style, since AI notes on different posts are not alike. Two preregistered predictions failed: AI notes do not share rating outcomes more than human notes, and similarity has not grown over time. The crowd on the writing side has become concentrated, and nothing in the system reports it.

## 1. Introduction

Agreement between witnesses is evidence only to the extent that they are independent. Condorcet's jury theorem makes the condition explicit [12]: a majority beats an individual only if the jurors err independently.

Community Notes builds on this. Its bridging algorithm displays a note when raters with different rating histories agree that it helps [1]. The independence check sits on the rating side. Writers were never checked, because they were scattered volunteers.

In September 2025 X opened the system to AI note writers: enrolled programs that read a feed of posts for which users requested a note, and submit notes without a human in the loop [5]. By May 2026 they wrote 41% of submitted notes and 52% of helpful ones [2]. Earlier studies measured the helpfulness, speed and sourcing of AI notes [2, 3, 4]. None compared AI writers with each other; Gong and Wu list "writer diversity and governance" as future work and note that similar helpfulness rates across writers may reflect "similar design choices", untested [2].

Writer independence matters even though writers do not vote. A second note that repeats the first reads as corroboration to raters and readers. Coverage that rests on few writers inherits their blind spots together. And language models err together: when two models are both wrong they choose the same wrong answer about 60% of the time [6].

**Contributions.** (1) A descriptive finding: six AI accounts act as one system and write about half of all shown notes. (2) A preregistered comparison of AI-AI and human-human note pairs on the same post, for shared sources and shared wording, with controls for time, post size and operator. (3) A cross-post baseline that separates shared style from shared content. (4) Two preregistered negative results that bound the claim. (5) Open code and tables.

## 2. Related work

**Community Notes.** Wojcik et al. describe the bridging algorithm and its effect on readers [1]. Mohammadi et al. find that about 8% of notes reach helpful status and that helpful notes arrive late [7]; Chuai et al. find no platform-wide drop in engagement with misleading posts [8].

**AI note writers.** Gong and Wu characterize 20 AI writers by volume, speed, coverage and helpfulness [2]. Purnell evaluates seven months of AI notes and recommends routing rater attention to the best writers [3]. Li and Bakker run their own AI writer in the field and find its notes rated more helpful than human notes by raters who saw both [4]. De et al. study collaborative notes, drafted by an LLM and refined with human feedback [9]. None measures similarity between writers or concentration among them.

**Correlated models.** Kim et al. show that errors of different LLMs are correlated, more so for stronger models [6]. Our study asks whether this homogeneity is visible in a deployed crowd system.

**Own prior work.** In an earlier Apart sprint we found that a monitor counting agreeing agents cannot tell agreement from shared origin (swarm-canaries). The link is conceptual; no code is reused.

## 3. Methodology

### 3.1 Data

X's public Community Notes files, downloaded 14 November 2026 (dump of 12 November): Notes, Note Status History, User Enrollment. We did not use Ratings. AI writers are participants whose `enrollmentState` starts with `api` (41 accounts, 39 with notes). The window starts at the first AI note, 2 September 2025. We keep non-collaborative notes classified as misleading: 340,170 notes on posts with at least two authors.

### 3.2 The fleet

Before any design decision we inspected the data. Six AI accounts wrote 52 to 55 thousand notes each, 86% of all AI notes. Five wrote their first note on the same day (17 December 2025). On 271,425 posts exactly one of the six wrote; on 25,810 exactly two; on 41 three; never more. When two wrote on one post, 42.5% of the pairs were less than a minute apart. We call these accounts *the fleet* and treat them as one author. The data cannot show who operates them.

### 3.3 Pairs, controls, weights

A pair is two notes on the same post by different authors, in the same language (py3langid), at most 24 hours apart. Groups: AI-AI (different operators under the fleet rule), human-human, AI-human, and fleet-fleet (reported separately).

Three things make notes look alike for reasons unrelated to shared models, and each has a control:

- **One system under several names.** Fleet counted as one author.
- **Time.** Median gap is 0.6 h for AI-AI pairs and 4.6 h for human pairs. We compare inside three windows (under 1 h, 1 to 6 h, 6 to 24 h) and reweight human windows to the AI-AI time profile.
- **Viral posts.** A post with n notes yields n(n-1)/2 pairs; 13.7% of human pairs come from posts with ten or more notes. Each pair gets weight 1 / (pairs of its group on that post).

### 3.4 Measures

**Sources (main).** URLs are normalized (host case, `www`, fragments, tracking parameters; YouTube video ids kept). Links to the post itself, search pages, `share.google` and X policy pages are dropped. Per pair: Jaccard overlap of the two URL sets, for pairs where both notes keep a link. Secondary: at least one shared URL, which is inflated when notes carry more links (fleet 2.4 per note, other AI 1.7, humans 1.4).

**Text (secondary).** Jaccard overlap of character 4-gram sets, links removed. Headline: the share of AI-AI pairs above the similarity that only the top 5% of human pairs in the same window exceed. Under human-like independence this is 5%.

**Uncertainty.** Cluster bootstrap over posts, 1,000 resamples, because pairs from one post are not independent.

### 3.5 Preregistration

All choices above, and the criterion "the 95% interval of the Jaccard difference includes zero" as refutation, were committed to `docs/decisions.md` before any similarity was computed. Later additions are in a dated change log and are labelled post hoc below. Three extensions (shared fate, trend, cross-post baseline) were registered with their own refutation criteria before they were run.

### 3.6 Reading pairs

To interpret a disagreement between the two source measures, 40 pairs were sampled (30 with Jaccard at least 0.5, 10 with none; half AI-AI, half human) and presented blind. The author labelled 27; a Gemini model <!-- TODO exact version --> labelled all 40 with the same three questions and no context. The model did not open links.

## 4. Results

### 4.1 One system writes half of what readers see

<!-- Figure 1: monthly share of shown notes by fleet / other AI / human, from extA_concentration_monthly.csv -->

The fleet's share of shown notes rose from 3.7% (December 2025) to 19.7% (March 2026) and 42.6% (April 2026). From April to November 2026 it wrote 51.2% of 61,119 shown notes, against 43.5% of submitted notes; all AI writers together wrote 56.5%.

Of 54,974 posts with a shown note in that period, all shown notes came from the fleet on 47.3%, and on 34.3% nobody else had written any note.

### 4.2 Sources: a small difference

| Group | Pairs | Jaccard | At least one shared link |
|---|---|---|---|
| AI-AI, different operators | 34,393 | 0.171 | 40.1% |
| Human-human, reweighted | 91,607 | 0.156 | 21.3% |
| Difference | | +0.015 [+0.010, +0.020] | +18.8 pts [+18.0, +19.6] |
| Fleet-fleet, under 1 h | 12,466 | 0.279 | 63.1% |

By the registered criterion the hypothesis is not refuted, but the effect is about a tenth of the human level. Post hoc checks: English pairs only, +0.019 [+0.014, +0.024]; without pairs under one minute, +0.011 [+0.006, +0.015].

The two measures disagree. Reading explains why (Section 4.5).

### 4.3 Text: a large difference

<!-- Figure 2: within-post vs cross-post similarity, AI-AI and human-human, from extD_cross_post.csv -->

| Group | Pairs above the human top-5% bar | Mean 4-gram overlap, under 1 h / 1 to 6 h / 6 to 24 h |
|---|---|---|
| Human-human | 5.0% (by construction) | 0.118 / 0.102 / 0.093 |
| AI-AI, different operators | 12.1% [10.8, 13.6] | 0.210 / 0.198 / 0.198 |
| AI-human | 6.0% [5.6, 6.4] | 0.129 / 0.127 / 0.120 |
| Fleet-fleet | 16.9% [15.0, 18.7] | 0.255 / 0.205 / 0.219 |

AI notes resemble each other, not human notes, and unlike human pairs they do not drift apart with time.

**Not copying.** Near copies (overlap at least 0.8) are 1.16% of human pairs and 0.05% of AI-AI pairs.

**Not house style (registered).** For pairs on *different* posts, same day and language, 0.0% of AI-AI pairs and 0.2% of human pairs exceed the bar; mean overlap is 0.033 and 0.027. The excess of within-post over cross-post similarity is larger for AI pairs by 7.3 points [6.9, 7.8]. The resemblance appears only when two AI writers address the same post.

### 4.4 Two predictions that failed (registered)

**Shared fate.** Among pairs where both notes have a decided status, the phi correlation of outcomes is 0.843 [0.785, 0.898] for AI-AI and 0.794 [0.766, 0.818] for human pairs; difference +0.049 [-0.015, +0.111]. Not supported. Outcomes are driven by the post and its raters. Power is limited: 95.6% of decided AI notes in these pairs are helpful.

**Trend.** AI-AI similarity in July to November 2026 against November 2025 to March 2026: sources +0.005 [-0.003, +0.013], text -0.009 [-0.019, +0.002]. Not supported. The resemblance was present from the start.

### 4.5 Reading

On "same evidence" the author and the model agreed on 17 of 27 pairs. Among high-overlap pairs, human pairs rested on the same evidence more often (author 7/9, model 14/15) than AI pairs (author 5/11, model 10/15): AI pairs with a shared link often share only part of their evidence. This is what "at least one shared link" counts as a full match, and it supports Jaccard as the main measure. A second label (obvious source or a choice) showed systematic disagreement between the two readers and is not used.

### 4.6 Robustness

| Variant | Source difference | AI-AI text above bar |
|---|---|---|
| Main | +0.014 | 12.1% |
| Fleet = 7 accounts | +0.028 | 12.9% |
| Fleet not merged | +0.051 | 14.4% |
| 3-grams | +0.014 | 14.4% |
| Bar at human top 10% | +0.014 | 43.1% (human 10%) |
| Windows 30 min / 3 h | +0.013 | 11.8% |

(Computed on the text-measure pair set, hence +0.014 rather than +0.015 in the first row.) Conclusions hold. Without the fleet merge the source difference more than triples, so the merge is the conservative choice.

## 5. Discussion

**What changed in the system.** The rating side of Community Notes still requires agreement across a divide. The writing side has become concentrated: one system supplies about half of the shown notes, and for a third of covered posts it is the only writer. This is not a claim that these notes are bad; raters judge them helpful, and most of these posts would otherwise have no note. It is a structural dependence with no signal attached. An error mode of that system, or its withdrawal, would affect a third of coverage at once.

**Different evidence, same words.** AI writers from different operators mostly consult different sources, which is good news for independence where it matters most. Yet given the same post they converge on wording 2.4 times as often as humans. The system's design gives a plausible cause: all AI writers read the same feed, answer within minutes [2], may start from the same public template, and run on a few model families. To a rater, two similar notes look like two confirmations.

**What it does not show.** No effect on rating outcomes was found, and resemblance is not growing. The claim is about concentration and resemblance, not about harm to accuracy.

**What could be done.** (a) Publish an operator field for AI writers, so one system is visible as one. (b) Report writer concentration and pair similarity as a standing health metric; our scripts compute both from public data. (c) When routing rater attention [3], treat near-duplicate notes on a post as one candidate.

**Next.** The Ratings file would show how much rater attention goes to redundant AI notes, and whether raters who saw both notes of a pair rate them alike.

## References

<!-- TODO Das: check every entry against the source before submitting; first names for [2]. -->
1. Wojcik, S. et al. Birdwatch: Crowd Wisdom and Bridging Algorithms can Inform Understanding and Reduce the Spread of Misinformation. arXiv:2210.15723, 2022.
2. Gong and Wu. Characterizing AI Fact-Checkers and Their Contributions on Community Notes. arXiv:2605.16566, 2026.
3. Purnell, S. AI Writers on Community Notes: An Evaluation of Seven Months of Data. R Street Policy Study No. 338, June 2026.
4. Li, H. and Bakker, M. A. AI Fact-Checking in the Wild: A Field Evaluation of LLM-Written Community Notes on X. arXiv:2604.02592, 2026.
5. X. Community Notes API documentation. https://docs.x.com/x-api/community-notes/introduction
6. Kim, E., Garg, A., Peng, K. and Garg, N. Correlated Errors in Large Language Models. ICML 2025. arXiv:2506.07962.
7. Mohammadi et al. From Birdwatch to Community Notes. arXiv:2510.09585, 2025.
8. Chuai, Y. et al. Did the Roll-Out of Community Notes Reduce Engagement With Misinformation on X/Twitter? CSCW 2024. arXiv:2307.07960.
9. De, S. et al. How Human Feedback Shapes AI-generated Community Notes. arXiv:2606.30905, 2026.
10. Jaccard, P. Étude comparative de la distribution florale dans une portion des Alpes et des Jura. 1901.
11. Efron, B. Bootstrap Methods: Another Look at the Jackknife. Annals of Statistics, 1979.
12. Condorcet. Essai sur l'application de l'analyse à la probabilité des décisions rendues à la pluralité des voix. 1785.

## Appendix A. Limitations and Dual-Use / Ethical Considerations

**What the results do not establish.** No note is shown to be wrong. Shared sources can be the correct sources; the human baseline separates this only in part. The fleet is identified by behaviour (volume, start dates, non-overlapping assignment, timing); one operator is an inference. A second cluster of six AI accounts posting within about a second of each other was not merged, because a shared feed explains its timing. AI status comes from an enrollment snapshot on the download date. Post text is not in the public data, so we could not control for sources already linked in the post. Notes still awaiting ratings make recent months provisional. The reading sample is small, and the labelling model did not open links. Similarity is lexical; paraphrase is not captured. The extensions and several checks were decided after the first result and are labelled as such.

**Dual use.** The signals that reveal one system behind several accounts (same-minute posting, non-overlapping assignment, similar wording) also tell an operator how to avoid looking like one system: stagger timing, vary wording. We judge the benefit of making concentration measurable to be larger, since the signals come from public data and the platform has stronger ones.

**Privacy and data.** All data is public and pseudonymous. We did not attempt to identify any participant or operator and name none. Note text is not redistributed; the repository contains code and aggregate tables only.

## Appendix B. Use of AI tools and prior work

Claude (Anthropic) wrote the analysis code, ran the computations, proposed method options and drafted text, working in the project folder at the author's direction. <!-- TODO Das: state honestly how much of the final text is yours after rewriting. --> The author made the method decisions marked in `docs/decisions.md`, read the pairs, and is responsible for all content. A Gemini model labelled the reading pairs. No code predates the sprint. Conceptual link to swarm-canaries (Apart Swarm Alignment sprint, November 2026), no code reused.

Code and tables: https://github.com/dassmod/independent-witnesses
