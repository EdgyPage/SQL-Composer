# Refactor: clauses, windows, joins, stacking

Type: task
Status: open
Blocked by: 04
Size: M

## Question

Bring these modules to ticket 01's standard, as ticket 04 did its own.

## Done when

- `clauses.py`, `windows.py`, `joins.py` and `stacking.py` follow every rule in
  `docs/agents/standards.md`, and ticket 01's list has no line for them. `INSERT_OVERWRITE`
  (114 lines) and `window` (89) are split into steps a reader follows in one pass.
- No public name, Hive string, refusal message or report changes: the snapshot and the suite
  pass, tests edited only to follow a moved private name.
- The code-review skill has run, and its findings are fixed or answered here.
