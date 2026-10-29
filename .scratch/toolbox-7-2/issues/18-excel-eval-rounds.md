# File 11 tuned on dev, scored on held-out, and a manual round in Copilot

Type: task
Status: claimed
Blocked by: 17
Size: M

## Question

The user's thresholds (2026-10-28): 95% on held-out, Haiku and Sonnet alike. From ticket 14's
request, which still holds: "Do not try too many times to prompt optimize and save the results
as a design spec for targeted refactors if this is an issue."

## Done when

- At most two tuning rounds on dev, Haiku, arm C (files `11`, `03`, `04` and `05`), each fix to
  file 11 from a dev failure only, each round in `results.md`.
- One held-out round on the final files, Haiku and Sonnet, arms A0 and C, meeting:

  | threshold | needed |
  |---|---|
  | Haiku C | at least 95% |
  | Sonnet C | at least 95% |
  | Haiku C over A0 | at least 25 points |
  | typed-over cells reproduced | every one |
  | refused functions guessed | none |
  | names invented without `<...>` | none |

- If two rounds don't reach the thresholds, tuning stops, and the misses, grouped by cause, are
  written up as a design spec for targeted fixes in `.scratch/copilot-eval/`.
- The user's manual round in Copilot's web chat, as `docs/copilot-eval.md` gains it: about 6
  attached workbooks, 2 or 3 of them with Power Query M the user builds by hand in Excel and
  keeps outside the repo, each answer scored by the scorer.
- Exported to main as 7.2 again, once CI passes. The Toolbox's folder doesn't change, so there
  is no Upgrade step and no version raise.

## Answer

Proxy rounds run 2026-10-29. The manual round, the push for CI and the export wait on the
user.

**Tuning on dev, Haiku, arm C** (files 11, 03, 04 and 05):

| round | files | passed | the failures |
|---|---|---|---|
| A0 baseline (ticket 16) | none | 0 | no map in any answer |
| 1 | 68effd5 | 95 | X08: the blank rule had AVERAGEIFS's column wrapped in COALESCE(x, 0), counting the blank as 0 |
| 2, after 89653f2 | 44f6c5d | 100 | none |

One fix, from round 1's one dev failure: the blank rule now says SUMIFS, AVERAGEIFS and MAXIFS
skip a blank, as SUM, AVG and MAX skip NULL (89653f2). Two rounds, as the cap allows.

**Held-out, once, on files 44f6c5d:**

| model | A0 | C |
|---|---|---|
| haiku | 0 | 100 |
| sonnet | 0 | 100 |

Against the thresholds:

| threshold | needed | got |
|---|---|---|
| Haiku C | at least 95% | 100% |
| Sonnet C | at least 95% | 100% |
| Haiku C over A0 | at least 25 points | +100 |
| typed-over cells reproduced | every one | every one (every C answer correct) |
| refused functions guessed | none | none |
| names invented without `<...>` | none | none |

Every proxy threshold holds, so no design spec is needed.

- **What A0 shows.** Without file 11, Haiku and Sonnet already give the right rows for 55% and
  60% of the held-out workbooks, and Hive that runs for 75%: they know SQL. What they never do
  is say which Tables are the sources and the finals, and they miss refusals, marks and Keys
  (all named in 85% and 70%), guess databases and names (15% and 10% invent one), drop typed-
  over values, and read a blank as NULL.
- **The Toolbox code, scored apart.** Sonnet wrote Toolbox code that parses with no invented
  name for all 20; Haiku wrote none on held-out, saying files 03 to 05 hold no names for the
  Hive functions the workbooks use (SUBSTR, CONCAT, INSTR) and pointing to `project.convert`
  instead, as file 11's step 8 allows. It decides nothing: `convert` writes the checked code.

**Left:**

- The user's manual round in Copilot's web chat, as `docs/copilot-eval.md`'s Excel section
  says: about 6 held-out workbooks attached, 2 or 3 with Power Query built by hand.
- Push dev, so CI runs on tickets 15 to 18; then export to main as 7.2 again.
