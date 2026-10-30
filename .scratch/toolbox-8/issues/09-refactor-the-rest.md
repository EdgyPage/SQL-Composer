# Refactor: lineage, comparisons, running, example_database, public, `__init__`, and tools/

Type: task
Status: open
Blocked by: 08
Size: L

## Question

The last of the Toolbox, and `tools/`. Ticket 01's list ends empty.

## Done when

- `lineage.py`, `comparisons.py`, `running.py`, `example_database.py`, `public.py` and
  `__init__.py`, and every file in `tools/`, follow every rule in `docs/agents/standards.md`.
- Ticket 01's list is empty, and the test that held it says so in its docstring (no list left).
  That includes the long lines (E501) it lists in `tests/` and `worked_examples/`, which no
  refactor ticket reads: each is wrapped, with no change to what a test checks or a how-to
  shows.
- No public name, Hive string, refusal message or report changes: the snapshot and the suite
  pass, tests edited only to follow a moved private name. The Copilot files and the eval
  results are unchanged, byte for byte.
- The code-review skill has run, and its findings are fixed or answered here. The drift review
  of the phase's last commit is clean, and the user is told the line count before and after.
