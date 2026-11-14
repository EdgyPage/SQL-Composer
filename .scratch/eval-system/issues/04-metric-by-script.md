# The Metric request evaluation by script, one agent per role

Type: task
Status: resolved
Blocked by: 01, 02
Size: M

## Question

A Metric request conversation is many turns between a stand-in user and Copilot; today each turn
is a fresh agent (Q7).

## Done when

- `metric_eval.py` uses `eval_runs` and writes under `.eval-local/`.
- A conversation is two agents, one per role, each spawned once with its first message and
  continued with `SendMessage` for later turns. The script writes each turn's text for the session
  to send, reads each reply, and ends the conversation by its rules (a request, or the turn cap).
- Each agent's usage is recorded per conversation in the ledger.
- `docs/copilot-eval.md`'s Metric request section says how in numbered steps.
- One dev task's conversation, run both ways, shows the token difference in the ledger.

## Answer

Built 2026-11-14: `tools/metric_eval.py` rebuilt on `eval_runs`, tests in
`tests/test_metric_eval.py`, the Metric request section of `docs/copilot-eval.md` rewritten as
seven numbered steps, `.claude/agents/metric-proxy.md`'s description updated. Everything is under
`.eval-local/`: a round in `metric/<round>/<task>/`, the table in `metric/results.md`, replies in
`memo/`, usage in `ledger.csv`.

**Commands** (each takes `--local`, a test's folder):

    plan <arm> --split dev --model haiku [--only M01 ...] [--fresh] [--over-budget]
    start <arm> --round <name> --split dev --model haiku [--only ...]   # writes folders, prints each task's first spawn
    next <task folder>                  # prints the one spawn or SendMessage to do; at the end writes transcript.md and request.md
    usage <task folder> --role copilot|user --tokens N --seconds S [--commit sha]
    score <round> <arm> --split dev --model haiku

`next` reads the folder's newest turn: after Copilot's turn 1 it prints the user agent's spawn
(its first message is user.md plus that turn); every later line is a `SendMessage` to the agent
already spawned, naming the turn file to read and the one to write. A conversation ends when
Copilot's turn holds a request, after `TURN_CAP` (12) of Copilot's turns, or, in A0, after its
one turn. The memo key is now the hash of the text the task loads (arm C: file 19 and the
definitions), with no files version; a reply carried over from the old memo keeps its key.

**Comparison** (task M01, arm C, haiku, the same script's folders, both ways stopped after six
Copilot turns and five user turns, neither yet holding a request, so the ledger result is "not
ended"). Rows are in the ledger under rounds `cmp-kept` and `cmp-fresh`:

- one agent per role: Copilot 25,733 tokens, user 18,903; total 44,636;
- a fresh agent per turn: Copilot 115,211 (six agents of 16,619 to 21,739, each rereading the
  file and every earlier turn), user 73,385; total 188,596.

The one-agent way used about a quarter of the tokens (4.2 times fewer), and the gap widens each
turn: a kept agent's report grew about 2,000 tokens a turn, a fresh agent's by about 1,000 but
from a start of 16,000. Caveat: a resumed agent's reported usage may be its running total; the
kept figures are the last report of each agent.

**Decided:** the `metric-proxy` agent type is registered when a session starts, so the comparison
ran the same instructions on `copilot-proxy` (also Read and Write only, haiku); a later session
spawns `metric-proxy` as the doc says. Subagents of a worktree session cannot write to the main
checkout, so the conversations ran in the worktree's own `.eval-local/` and only the ledger rows
went to the main checkout's. `--only` was added so one task can be run.

## Code review

Run with this ticket as spec, fixed point 3de80309 (review-standards and review-spec, sonnet).

- Fixed: `next_step` renamed `advance` (it writes the transcript at the end) and
  `write_task_messages` renamed `write_task_folder` (it also writes the conversation record);
  `score_round` reads the memo only in the branch that needs it and counts on its own line; the
  doc says A0 ends as `ended: no request in turn 1` and that `--role user` is arm C only; the
  ticket's Status is resolved.
- Answered: the comparison is stopped at six Copilot turns, not run to a request, to bound its
  cost, and said so above; the ledger rows are local, so the numbers are in the Answer. The
  ledger accepts any result text for the metric pipeline (only maintainer rows are checked).
- Left, as judgement calls: `memo_key`'s unused `reply` (the memo's key function shape, in its
  docstring); the free-text reason in `ending` doubling as the ledger result; `round` as a field
  name; `_parser`'s per-command `if` on the name; `datetime.date.today()` three times.
