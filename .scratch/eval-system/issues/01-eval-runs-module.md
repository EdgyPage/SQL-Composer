# tools/eval_runs.py: ledger, memo by loaded text, plans, budgets

Type: task
Status: open
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
