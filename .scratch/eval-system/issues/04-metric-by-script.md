# The Metric request evaluation by script, one agent per role

Type: task
Status: open
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
