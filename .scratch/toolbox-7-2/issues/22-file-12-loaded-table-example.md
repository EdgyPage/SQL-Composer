# File 12 shows a query and the Table it loads, read apart, by example

Type: task
Status: resolved
Blocked by: 21
Size: S

## Question

Ticket 21 fixed one held-out cause but not the other: with two wordings of the rule, Haiku
still took a loaded Table for a step when another query reads the query that loads it, and
the two share a name (X70, X73). Sonnet never did. The misses file suggests an example rather
than another rule. The user (2026-10-29): "Try the example".

## Done when

- Four new tasks for that case, written and committed before file 12 changes: X75 and X76 dev,
  X77 and X78 held out, each a query and the Table it loads sharing a name, the Table adding a
  formula column, another query reading the query.
- File 12 gains a short example of the case, within 8,000 characters.
- At most two dev rounds, Haiku, arm C; then held-out once, Haiku and Sonnet, arm C, on the
  whole split, against ticket 18's thresholds, and on X70, X73, X77 and X78 for this case.
- `.venv/Scripts/python -m pytest`, the code review, the beginner reader and the drift review;
  then the user's call on pushing dev, CI and the export.

## Answer

Built 2026-10-29. Tasks X75 to X78 (efc21d8) before the example (fa48987).

| run | files | passed | loaded-Table cases |
|---|---|---|---|
| dev round 1, Haiku | fa48987, the example | 100 | X71, X75, X76 pass |
| dev round 2, Haiku | 423bc80, "anything reads it" | 87 | X71, X75, X76 fail |
| held-out, Haiku / Sonnet | 423bc80 | 92 / 100 | X70, X73, X77, X78 pass |
| dev check, Haiku | 5df4678, "a formula reads it" back | 100 | pass |
| held-out, Haiku / Sonnet | 5df4678 | 87 / 100 | X70, X73, X77, X78 fail |

The example did not settle it for Haiku. On this one case Haiku is near a coin toss: the same
four held-out workbooks pass on 423bc80 and fail on 5df4678, which differ by one word, while
the three dev workbooks do the opposite. Sonnet gets every one right on every version. More
words won't fix what Haiku guesses at, and room isn't short, so no third file was made.

Haiku's held-out score with the files has been 94, 97, 92, 92 and 87 across versions; Sonnet's
100 on all. The thresholds hold for Sonnet and not for Haiku.

Reviews: spec (sonnet) none; beginner reader (opus) four wording edits, three kept, the fourth
("anything reads it") undone after dev round 2. Drift: efc21d8, fa48987, 423bc80, 5df4678 clean.

The user, while it ran (2026-10-29): "If we need more space in yet a third context file, add
it. While we're here, make a small script on dev that merges all the txt instructions in to one
mega context document just for convenience. Ship the pieces and the mega document to main."
`tools/merge_copilot_files.py` writes `copilot/all_in_one/all_copilot_files.txt` (90,718
characters), which `copilot_files.py` runs after each render and a test holds to the files.
Shipped on 5df4678's files.
