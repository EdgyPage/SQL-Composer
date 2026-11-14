# The Copilot and Excel evaluations run by script

Type: task
Status: resolved
Blocked by: 01, 02
Size: M

## Question

Rounds without an orchestrating worker (Q2).

## Done when

- `copilot_eval.py` and `excel_eval.py` use `eval_runs` for the memo, plans and the ledger, and
  write runs under `.eval-local/`.
- A round is: `plan` (the tasks to ask, the estimate); `batch`, which writes each proxy's
  message file and prints one line per proxy to spawn (agent type, model, the one-line prompt);
  the session spawns them; `collect`, which reads the replies; `score`, which scores and keeps
  them; `record` per agent from its reported usage.
- Arms C and R and the Excel arm C all work this way; routing (arm R) is scored by its rules
  strict and by the Index, deterministically, where today it was scored by hand.
- `docs/copilot-eval.md` says how, in numbered steps a fresh agent can follow with no other
  context.

## Answer

Built 2026-11-14: `tools/copilot_eval.py` and `tools/excel_eval.py` on `tools/eval_runs.py`;
tests in `tests/test_eval_rounds.py` and `tests/test_eval_runs.py`; `docs/copilot-eval.md`
rewritten (its Metric request section untouched, for ticket 04); `.claude/agents/copilot-proxy.md`
now writes no header lines.

A round, by `tools/copilot_eval.py` or `tools/excel_eval.py`, all with `--local` for a test:

    plan <arm> --split S [--objective O | --tasks X01,..] --model M [--fresh] [--over-budget]
    batch <arm> (same) --round NAME      # writes .eval-local/<pipeline>/runs/NAME/<proxy>/message.md,
                                         # prints "copilot-proxy | <model> | <one-line prompt>" per proxy
    (the session spawns each line)
    collect NAME                         # merges the proxies' answers.md into NAME/answers.md; exit 1 if any reply is missing
    score NAME                           # or an answers file; keeps replies in the memo, adds a row to copilot/results.md
    .venv/Scripts/python tools/eval_runs.py record --pipeline copilot|excel --role proxy --round NAME --task <proxy> ...

**Decided:**

- `eval_runs` gained the shared machinery: `Pipeline`, `add_round_commands`, `run_round_command`,
  `Batch`, `write_batch`, `collect_batch`, `answers_to_score`, `round_replies`, `keep_round`,
  `memo_line`, `read_answers`, `files_version`, `chunks`. `RoundToPlan` takes `held_out` (`--fresh`
  leaves those) and `agents` (the estimate is by proxy: one ledger row per proxy).
- Keys hold the hash of the loaded text alone; `files_version` is gone from the new pipelines, so a
  held-out task is asked once per version of the text it loads. `eval_memo` stays, with its
  files-version planning, for `metric_eval` until ticket 04; its pure tests stay in
  `tests/test_eval_memo.py`, and the Copilot and Excel ones moved to `tests/test_eval_rounds.py`.
  `eval_memo.files_version` is now `eval_runs`'.
- Proxies: arm C one per objective (`c03`), other arms 10 tasks each (`r-1`), Excel 5 each (`c-1`).
  `batch` refuses an existing round name; a round that asks nothing writes its folder with no
  proxy and is scored from the memo.
- Arm R: `routing` scores strict (one existing file named, the task's objective's) and by the
  Index (the first file named is one an Index row for that objective loads, read from file 00
  live), no model. Row: `| date | files | model | R | split | n | strict | index | from memo |`.
- `tools/eval_runs.py` line 130's over-long line (from ticket 08) fixed so ruff passes.

## Code review

Run with this ticket as spec, fixed point 3de80309 (review-standards and review-spec, sonnet).

- Fixed: lambdas replaced by named functions; `x or default` replaced by `if`s; `_shown` renamed
  `path_for_proxy`; the shared results file is one constant, `RESULTS`.
- Answered: `read_answers` keeps its name (moved from `eval_memo`, same name in `metric_eval`'s
  use); the id-to-Task adapters in each tool are one-liners over different task tables;
  `Pipeline` has many callbacks because the two tools differ in tasks, filters and messages;
  arm R's branch in `copilot_eval.score` has one user; `eval_memo` keeps files-version planning
  because `metric_eval` still uses it (ticket 04). The spec reviewer's "scope creep"
  (`carry_over`, `copy_records`) is ticket 02's, not in this diff.
