# File 11 tuned on dev, scored on held-out, and a manual round in Copilot

Type: task
Status: open
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
