# Data notes (step 1, 14 Nov 2026)

What the dump looks like, checked before any method decision. Numbers from `src/02_inspect.py`.

## Files

| File | Rows | Note |
|---|---|---|
| notes-00000.tsv | 3,238,446 | All regular notes, Jan 2021 to 12 Nov 2026 |
| notes-00001..00004.tsv | 77,077 total | Only collaborative notes (`isCollaborativeNote=1`), all by a single participant, Jan to Nov 2026 |
| noteStatusHistory-00000.tsv | 3,524,125 | ~208k more rows than notes (deleted notes keep status rows, to check) |
| userEnrollment-00000.tsv | 1,517,274 | Current snapshot |

- Author column in Notes and Status History is `noteAuthorParticipantId` (not `participantId` as the docs say). Renamed to `participantId` in `01_load.py`.
- Row counts match `wc -l` exactly: no line breaks inside note text, no shifted columns (classification and flag columns hold only valid values).
- Every note author has an enrollment row.

## AI writers

- 41 participants with `apiEarnedIn`; no `apiEarnedOut` or `apiTestUser` in this snapshot. 39 of them have notes.
- First AI note: 2 Sep 2025. Window for the study starts there.
- 374,441 AI notes vs 860,545 human notes in the window (collaborative notes excluded).
- AI share of new notes by month: 0.5% (Sep 2025), 10% (Jan 2026), jump to 38.5% (Apr 2026), 50.7% (Oct 2026).
- **Concentration:** six writers wrote 52 to 55 thousand notes each (323k, 86% of all AI notes). Five of them started on the same day, 17 Dec 2025, the sixth on 24 Nov 2025. Very likely one operator. This is the "one operator, several writers" confound from the plan, visible in the data.

## Posts and pairs (window, non-collaborative)

- 909,193 posts with at least one note; 220,838 with two or more.
- Pairs of notes by different authors on the same post:

| Group | Pairs | Posts | Median gap between the two notes |
|---|---|---|---|
| AI-AI | 61,154 | 47,783 | 0.6 h |
| AI-human | 95,128 | 58,025 | 2.8 h |
| human-human | 374,591 | 138,901 | 4.6 h |

- Of the AI-AI pairs, 25,936 are between two of the six-writer fleet, 27,619 have one fleet member, 7,599 have none.
- Fleet pairs often land within the same minute.

## Links

- 100% of AI notes contain a link (2.31 per note); 88% of human notes (1.36 per note).
- t.co short links are rare (0.1% AI, 0.6% human): URLs are full, so domain extraction needs no expansion step.
- Median note length: 350 characters AI, 243 human.

## Open for step 4 and 5 (Das decides)

- The fleet: treat the six as one writer, exclude fleet-internal pairs, or report them as their own group.
- Gap matching: AI-AI pairs are much closer in time than human pairs, so time gap has to be controlled.
- Many-note posts weigh heavily in pair counts (one post with 12 notes gives 66 pairs); weight per post or cap.
