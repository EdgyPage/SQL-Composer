# The Copilot and Excel evaluations run by script

Type: task
Status: open
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
