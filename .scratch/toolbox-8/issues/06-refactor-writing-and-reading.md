# Refactor: writing, engine, trees, converting

Type: task
Status: open
Blocked by: 05
Size: L

## Question

Bring these modules to ticket 01's standard. They are the three that may import sqlglot, and
the Toolbox's own tree, so the tree walks the survey found in three styles get one.

## Done when

- `writing.py`, `engine.py`, `trees.py` and `converting.py` follow every rule in
  `docs/agents/standards.md`, and ticket 01's list has no line for them. The `_stop`s in
  `engine.py` go through `refuse`, as ticket 03 set; `converting.py`'s chained conditional
  expressions and its two-`for` comprehensions are plain.
- No public name, Hive string, refusal message or report changes: the snapshot and the suite
  pass, tests edited only to follow a moved private name.
- The code-review skill has run, and its findings are fixed or answered here.
