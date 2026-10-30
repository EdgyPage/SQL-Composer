# Refactor: refusals, conditions, calculations, kinds, keys, describe

Type: task
Status: open
Blocked by: 03
Size: M

## Question

Bring these modules to ticket 01's standard. The user (2026-10-30): "less code to review that
I actually understand".

## Done when

- `refusals.py`, `conditions.py`, `calculations.py`, `kinds.py`, `keys.py` and `describe.py`
  follow every rule in `docs/agents/standards.md`, and ticket 01's list has no line for them.
- No public name, Hive string, refusal message or report changes: the snapshot and the suite
  pass, tests edited only to follow a moved private name.
- Each unclear private name the survey found here is renamed (`keys._keeps`, `keys.unproven`,
  `keys._listed`, `keys._held`, `keys._plain`, `describe.ask`, `describe._held`, and the like).
- The code-review skill has run, and its findings are fixed or answered here.
