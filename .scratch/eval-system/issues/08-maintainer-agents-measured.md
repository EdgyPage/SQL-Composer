# The maintainer agents measured

Type: task
Status: resolved
Blocked by: 01
Size: S

## Question

The user suspects the drift reviewer, code reviewer and beginner reader slow development "with
wasted work but I don't have proof" (Q1, Q13).

## Done when

- The ledger takes a maintainer agent's run: which agent, which commit or ticket, its tokens and
  seconds, and whether it opened an item or a finding.
- CLAUDE.md's Maintainer agents section and the drift hook's message tell the session to record
  each run with `eval_runs record`.
- Nothing about when or how the agents run changes: the data decides that later.

## Answer

Built 2026-11-14. Pipeline and role are both `maintainer`; the other columns carry the rest,
so the ledger's fields are unchanged:

- `task` is the agent: `drift-reviewer`, `code-review-standards`, `code-review-spec` or
  `beginner-reader` (`eval_runs.MAINTAINER_AGENTS`);
- `round` and `commit` are the ticket or commit reviewed; `arm` is `-`; `model` is `opus` or
  `sonnet`;
- `result` starts `clean` or `opened`, then the items or findings ("opened D3 D4", "opened 2
  findings"). `check_maintainer_run` refuses any other task, role or result, so the data stays
  countable.

The command, in CLAUDE.md's Maintainer agents section and, as `RECORD_RUN` in
`.claude/hooks/drift_list.py`, in the drift hook's review request:

    .venv/Scripts/python tools/eval_runs.py record --pipeline maintainer --role maintainer --task <agent> --round <commit or ticket> --commit <commit> --arm - --model <model> --tokens <tokens> --seconds <seconds> --result "<clean | opened ...>"

Tests: `tests/test_eval_runs.py` (each agent records; a bad task, role or result is refused),
`tests/repo/test_hooks.py` (the request carries the command). No agent's cadence or prompt
changed. The stop hook's message is unchanged: the request already carries the command.

## Code review
