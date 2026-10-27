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
