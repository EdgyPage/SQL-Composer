# The Copilot files tuned on dev, and scored on held-out

Type: task
Status: open
Blocked by: 13
Size: M

## Question

Show the files make a positive difference, as the user asked, by the thresholds the plan set.

The user (2026-10-27), while ticket 13 was built: "If the prompt and test loop does not get
perfect results after a few iterations, it may be justified to consider agentic readability as
part of the workflow for a code refactor. Do not try too many times to prompt optimize and save
the results as a design spec for targeted refactors if this is an issue."

## Done when

- Tuning rounds on the dev split (Haiku; A1 and C twice a round) each recorded, the files fixed
  only from dev failures.
- One held-out round per files version: Haiku and Sonnet, arms A0, A1, C and R (routing), in
  `.scratch/copilot-eval/results.md`, against the thresholds: Haiku C at least 25 points over
  A1 and at least 70%; Sonnet C at least 85%; no objective lower in C than in A1; routing at
  least 90%; invented names in at most 5% of C's answers; at most one needless opt-out in C.
- The user's manual round in Copilot's web chat, by `docs/copilot-eval.md`: C at least 20
  points over A1.
- At most three tuning rounds. What still fails after them is written up as a design spec for
  targeted refactors that would make the Toolbox easier for a model to use, as the user asked,
  not tuned further.

## Answer

All rounds are in `.scratch/copilot-eval/results.md`, and the raw answers in its `runs/`, so a
changed scorer can score them again.

**Tuning on dev (Haiku): two rounds, no third needed.**

| round | files | A0 | A1 | C |
|---|---|---|---|---|
| baseline (ticket 12) | none | 20 | 30 | - |
| 1 | 353cbeeb | | | 100 |
| 2, after ticket 13's reviews | 95fbcd5 | | | 100 |

The plan asked for A1 and C twice a round, to see the noise. C passed 20 of 20 in both rounds.
A1 ran once, as the baseline, because with C at 100 the noise couldn't change a verdict. No file
was changed for a dev failure, because there was none.

**Held-out, once, on files 95fbcd5:**

| model | A0 | A1 | C | routing |
|---|---|---|---|---|
| haiku | 0 | 0 | 100 | 90 |
| sonnet | 0 | 0 | 90 | 90 |

Against the thresholds:

| threshold | needed | got |
|---|---|---|
| Haiku C over A1 | at least 25 points | +100 |
| Haiku C | at least 70% | 100% |
| Sonnet C | at least 85% | 90% |
| no objective lower in C than in A1 | - | every objective is 100 in C and 0 in A1 |
| routing | at least 90% | 90% for both |
| invented names in C | at most 5% of answers | 0% |
| needless opt-outs in C | at most one | one (Sonnet) |

Every proxy threshold holds.

- **Sonnet's one failure, T27.** It moved the bound into `ON=` as asked, then added
  `many_matches=True` on its own. The Toolbox does warn there (the reference raises a
  RepeatedRowsWarning: job_runs is told apart by run_id, not job_id), and the request, "every
  job with its runs", does want the repeats, the case where file 04's step 5 allows the opt-out. So the answer is
  defensible. The scorer counts it because the reference leaves the warning showing. I kept
  the score rather than change a held-out reference after seeing the answers.
- **Routing's one miss, the same for both models.** T03, "count the alerts ... and run it",
  objective 01, was routed to 03, building a Statement. Haiku, given file 03, answered T03 and
  passed (`runs/2026-10-27-haiku-R-held_out/T03-with-03/`), so the route still reaches working
  code.
- **What the baselines show.** Without a file, every model wrote SQL's words as Toolbox names:
  - `COUNT`, `AVG`, `CASE`/`WHEN`/`ELSE`, `AND`/`and_`, `LAG`, `alias`, `greater_than`,
    `INNER_JOIN`;
  - guessed keywords: `Table(not_summed=/never_sum=/non_additive=)` and
    `check_key(dt_from=, dt_to=)`.

  The README's opening (A1) didn't stop any of them on held-out.

**No design spec.** The user said to write one if the files didn't get near-perfect results after
a few rounds. They did, in two, so there is nothing to spec. If a refactor for model use is ever
weighed, the baseline guesses above are where to start: aliases that refuse with the right name,
such as `COUNT` saying "count_rows", would help a model that has no file.

**Left: the user's manual round** in Copilot's web chat, as `docs/copilot-eval.md` says. Its
threshold is C at least 20 points over A1. The ticket stays open until it is scored.
