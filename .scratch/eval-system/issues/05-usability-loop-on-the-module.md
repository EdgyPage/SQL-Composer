# The usability loop on the module

Type: task
Status: resolved
Blocked by: 01, 02
Size: M

## Question

The usability loop keeps its own memo and its runs in git (Q2, Q4, Q9).

## Done when

- `usability_loop.py` keys each scenario's memo through `eval_runs` (its inputs as today), writes
  runs, transcripts and results under `.eval-local/`, and records each phase agent's and routed
  question's usage in the ledger.
- `prepare` prints the one-line prompt to spawn each phase's agent; routing a question prints the
  proxy to spawn, as ticket 03's batches do.
- `docs/usability-loop.md` says how in numbered steps.

## Answer

Built 2026-11-14: `tools/usability_loop.py` on `tools/eval_runs.py`, tests in
`tests/test_usability_loop.py`, `docs/usability-loop.md` rewritten as numbered steps.

- **Memo through `eval_runs`, on the same inputs.** A scored run is kept in `.eval-local/memo/`
  under the key of its slot: task `<scenario>-<n>` (the run's number in its round, from its name
  `<date>-<scenario>-<n>`), arm `run`, model `haiku`, the hash of the scenario's text, and, as
  the text loaded, `inputs_hash`, which is still made from exactly what the scenario's path reads
  (Toolbox 8.7, ticket 01). Its score is `pass` or `fail`. A scenario is memoized when every slot
  of its round holds a passing run and none a failed one; a failed slot is asked again; a run
  whose slot passed is refused by `prepare` unless `--fresh`.
- **Local only.** Runs are copied to `.eval-local/usability/runs/`, rows to
  `.eval-local/usability/results.md` (`OLD_RECORDS`' targets), the memo to `.eval-local/memo/`.
  The working run folders stay in the temp folder, outside the repo, so an agent finds nothing of
  dev's. `KEPT` and `RESULTS` are gone; tests set `LOCAL`.
- **Agents to spawn.** `prepare` prints `Run folder: ...` then one line per phase; `route` and
  `answer` one line for their proxy; each `<agent type> | <model> | <prompt>`
  (`zero-context-user | haiku | Read <run>/_loop/phase_<n>.md and follow it.`;
  `copilot-proxy | haiku | Message file: ... Answers file: ... No header lines.`).
- **Ledger.** `usage <run> phase-<n>|route-<n>|answer-<n> --tokens --seconds --result
  [--round] [--commit]` records a row (pipeline `usability`; role `user`, arm `phase` for a phase
  agent; role `proxy`, arm `question` for a routed question's proxy; task `<run>/<what>`).
  `plan` estimates the round from the past `phase` rows (routed questions are extra) and checks
  `eval_runs.BUDGET`, with `--over-budget` and `--fresh`.
- **`migrate`** keeps each row of `results.md` in the memo, from the inputs hash in its kept
  `inputs.json`, so scenarios scored before this ticket aren't asked again (a row from before
  8.7's inputs never matches, as before).
- `tools/workflows_page.py`'s comment names the new `results.md`. `copilot_eval.py`,
  `excel_eval.py`, `metric_eval.py`, `eval_runs.py` and `docs/copilot-eval.md` are untouched.

**Decided:** the line format `<agent type> | <model> | <prompt>` is this ticket's reading of
"one printed line per agent"; ticket 03's batches should match it, or this should follow
them. The round estimate counts phase agents only. A run with an `inputs.json` whose name ends in
no number is refused by `score --record`, before anything is kept.

## Code review

Run with this ticket as spec, fixed point 3de80309 (review-standards and review-spec, sonnet).
- Fixed: `plan_scenario` read the memo twice (now once); `migrate_results`' counter renamed
  `runs_kept`.
- Answered: `plan` stays a thin text wrapper over `plan_scenario`, because the existing tests
  and the doc call it; `key_of_slot`'s unused `reply` argument fits `eval_runs.memo_plan`'s
  `key_of` signature; `estimate_line` refuses over budget as well as returning the line, which
  its docstring says, since the budget check needs the estimate it prints; `record_usage` exits
  with `SystemExit` as `eval_runs`' own commands do, `ValueError` being this file's habit for the
  Project-making code; the `phase`, `route` and `answer` words and the `kept`/`passed` test are
  small repeats a shared helper wouldn't make plainer ("Simple over short").
- Spec axis: nothing missing. `migrate` and `--fresh`/`--over-budget` go beyond the Done-when
  and are kept: `migrate` so scenarios scored before this aren't re-run, the flags from the map's
  Notes on `plan`. The memo is keyed per slot, which the Answer states. The `<agent type> |
  <model> | <prompt>` line format must match ticket 03's; the parent merges both.
- Left: `usability_loop.py` is long (it already was); `estimate_line` and `record_usage` could
  move into `eval_runs` if another pipeline needs them.
