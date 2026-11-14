# The model ladder and caps

Type: task
Status: resolved
Blocked by: 01
Size: S

## Question

A task with a deterministic answer and input should cost as little as it can (Q5).

## Done when

- `eval_runs` keeps, per task, the cheapest model that has passed it; `plan` proposes that model
  and the round can override it.
- Each pipeline has a cap on a proxy reply's length and a conversation's turns, named in one
  place, which the batch writes into each message and the scorer holds.
- `plan` never re-asks a task whose memo key is unchanged, and says so per task.

## Answer

Built 2026-11-14: a headed section, "The model ladder and the caps", in `tools/eval_runs.py`;
small edits in `tools/copilot_eval.py`, `tools/excel_eval.py`, `tools/metric_eval.py` and
`tools/usability_loop.py`; tests in `tests/test_eval_ladder.py` and the pipelines' own test
files; a section of `docs/copilot-eval.md`.

**The ladder.** `LADDER = (haiku, sonnet, opus)`; `RUNGS` shortens it per pipeline (usability:
haiku only, as a larger model passing shows nothing of the docs). It is not kept in a file of
its own: it is read from the memo, where each reply holds its score. `ladder_step` walks a task
up by the replies kept under its key now: the first rung with none is where it is asked; the
first rung whose score passed (`score_passed`, which reads each pipeline's score line) gives its
reply; a task every rung failed is not asked again. `cheapest_passed` reads the cheapest model
that passed a task on any text, and the plan names it beside a task it asks. `plan` with no
`--model` (the default is `ladder`) proposes each task's rung, lists each rung's tasks and
sums the estimate by rung; any `--model` given overrides it for every task. `batch`, `prompts`,
`template`, `start` and `score` refuse `ladder`, since a rung is a round of its own: `--model
<rung> --only <its tasks>`. `--only` is new on the Copilot and Excel commands (Metric had it).

**The caps**, `eval_runs.CAPS`, reply in characters and turns:

| pipeline  | reply  | turns |
|-----------|--------|-------|
| usability | 8,000  | 5 (a run's questions) |
| copilot   | 6,000  | 1 |
| excel     | 12,000 | 1 |
| metric    | 6,000  | 12 (Copilot's turns) |

Sized from the largest replies in the local memo (Copilot 1.9k, Excel 5.8k, Metric 3.8k).
`TURN_CAP` and `MOST_QUESTIONS` are gone into the table. Each batch writes the cap into its
messages (`cap_text`); Metric's go into `copilot.md` and `user.md`, written beside the key's
text so the key is unchanged.

**Flagged, not failed.** The ticket and the map's Notes don't say; a reply over its reply cap is
flagged `OVER CAP` in its score line and the report and its score is unchanged: a long answer
isn't a wrong one, and a fail would put a correct answer in the memo as a failure the ladder
climbs on. A turn past the turn cap is held as before: Metric ends the conversation with no
request, and a usability run over its question cap fails. Metric flags a turn file over the cap
and Copilot's turns past the cap; usability lists the question replies over the cap.

**Never re-asked on an unchanged key.** Checked and tested for Copilot, Excel (plan), Metric
(plan) and the ladder: a task with a reply kept under its key is `from the memo` and not asked,
a failed one too; only `--fresh` asks a dev task again. One exception stays, ticket 05's: the
usability loop asks a slot again whose kept run failed with the same inputs; its plan says
which run failed. Say if that should stop.

**Decided:** a task's rung is judged by the replies under its key now; a pass on older text is a
hint in the plan, not an answer. A round on the ladder is several rounds, one per rung, since a
batch, its answers header and its memo keys hold one model.

## Code review

Run with this ticket as spec, fixed point c1bc8824 (review-standards and review-spec, sonnet).

- Fixed: the `KeyForModel` alias is gone (plain types); the three key-function hints agree;
  `refuse_the_ladder` is `check_not_the_ladder`; the over-cap block the Copilot and Excel
  scorers repeated is `eval_runs.hold_reply_caps`; usability's `replies_over_cap` is
  `long_question_replies` (no longer the name of another function's near twin); a dense
  comprehension in Metric is a loop; a missing return hint in the test.
- Answered: a reply over the cap is flagged, not failed (above); the spec reviewer reads
  "holds" as fail, so the user may want to say. The usability loop's re-ask of a failed slot is
  ticket 05's rule, kept and named above. Nothing is stored beyond the memo: "keeps" is read
  from it, as the Done-when allows. Metric's turn flag is reachable (a session that ignores
  `next` writes turns past the cap), and tested. Copilot's and Excel's turn cap of 1 is the
  one chat per task; no code needs to hold it. The `OVER CAP` flag stays in the kept score line;
  `score_passed` reads only its first words. Metric's `plan_of` names no held-out tasks, as
  before. `rung` and `ladder` aren't in CONTEXT.md: they are tooling words of this dev-only
  system.
- Left, as judgement calls: `ladder_plan` is long; `RUNGS` and `CAPS` are two per-pipeline
  tables; `score_passed` parses the score line by word position.
