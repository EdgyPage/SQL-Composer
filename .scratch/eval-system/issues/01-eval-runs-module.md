# tools/eval_runs.py: ledger, memo by loaded text, plans, budgets

Type: task
Status: resolved
Blocked by: -
Size: L

## Question

One module every testing pipeline plugs into (Q2 to Q5, Q8, Q10, Q15).

## Done when

- `tools/eval_runs.py` holds, each with tests:
  - **the local folder:** `LOCAL = <repo>/.eval-local/`, made on first use, and every path the
    module writes is under it;
  - **the ledger:** `.eval-local/ledger.csv`, one row per agent run: date, commit, round id,
    pipeline, task, arm, model, role (proxy, user, Copilot, maintainer), input tokens or total
    tokens as reported, seconds, result; a `record` command the session runs from an agent's
    reported usage, and a reader;
  - **the memo:** each reply keyed on its task's id and text, arm, model and the hash of exactly
    the text that task loads, dev and held-out alike; `tools/eval_memo.py` folds in, its tests
    kept;
  - **plans:** `plan` lists, for a round, each task to ask and why (no reply kept, its loaded
    text changed, `--fresh`), the rest from the memo, and the round's estimated tokens from past
    ledger rows of the same pipeline, arm and model;
  - **budgets:** `BUDGET = {pipeline: math.inf}`; `plan` refuses a round over its pipeline's
    budget unless `--over-budget`, so the check runs today and a number is one edit later.
- Existing memo replies are carried over into `.eval-local/memo/` under the new keys where their
  loaded text can be worked out, or re-asked on first need.
- Nothing in the module calls the network; the offline policy and code audit pass.

## Answer

Built 2026-11-14: `tools/eval_runs.py`, tests in `tests/test_eval_runs.py`.

The interface, for tickets 02 to 09:

- Commands: `record --pipeline --round --task --arm --model --role --tokens --seconds --result
  [--commit] [--date]`, `ledger`, `carry-over [--old]`; each takes `--local` (a test's folder).
- Folder: `LOCAL`, `MEMO`, `make_local_path(*parts, local=)`, which makes the parent and refuses
  a path outside `LOCAL`.
- Ledger: `Run`, `PIPELINES`, `ROLES`, `record_run`, `read_ledger`, `LEDGER_FIELDS`.
- Memo: `Key`, `hashed_key`, `Kept`, `write_kept`, `read_kept`, `kept_reply`, `text_hash`,
  `carry_over`; `tools/eval_memo.py` imports these and keeps its own plan, answers and
  `files_version`.
- Plan: `RoundToPlan(pipeline, arm, model, tasks)`, `memo_plan`, `plan_round(asking, key_of,
  fresh, over_budget, local=, budget=)` giving `RoundPlan(asked, tokens, text)`,
  `estimated_tokens`, `check_budget`, `BUDGET`.

**Decided:**

- A pipeline's own `plan` command (tickets 03 to 05) calls `plan_round` and gives it `--fresh`
  and `--over-budget`; the module has no tasks of its own, so it has no `plan` command.
- The storage moved out of `eval_memo`, so there is one file format. `eval_memo`'s held-out
  files-version planning stays until tickets 03 to 05 move the pipelines, so `Key.files_version`
  is kept, defaulting to "-", and a key made through `plan_round` leaves it out. Its tests are
  unchanged and pass.
- Carry-over copies the old files unchanged: each holds its loaded-text hash, so the keys are
  the same. It is a command, not run here: `.eval-local/` is local, and ticket 02 owns the
  `.gitignore` entry and the move.
- The ledger has one `tokens` column, the total as reported (input tokens where only those are
  known, said in `result`); the estimate is a mean over rows of the pipeline, arm and model.
- `Run` fields stay strings, as the CSV holds them; `check_run` validates the numbers.
- No estimate (no past row) passes the budget check: there is nothing to check it by.
- The commit is passed with `--commit`, not read from git: no subprocess in the tool.
- `tests/repo/test_pointers.py` exempts `.eval-local/`, which CLAUDE.md names and a fresh clone
  lacks.

## Code review

Run with this ticket as spec, fixed point dd2965b2 (review-standards and review-spec, sonnet).

- Fixed: `local_path` renamed `make_local_path` (it makes a folder), `_ledger` renamed
  `_print_ledger`.
- Answered above: no `plan` command; held-out files-version keys stay in `eval_memo` until the
  pipelines move; carry-over copies unchanged; the re-export in `eval_memo` is the fold-in's
  interim; `.gitignore` is ticket 02; one `tokens` column; string fields; the pointers
  exemption.
- Left: `write_kept` and `carry_over` take any folder (the pipelines' tests pass temporary
  ones); `make_local_path` guards the ledger and whatever callers route through it.
