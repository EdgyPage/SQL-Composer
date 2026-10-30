# Refactor: tables, admin, upkeep, unchecked, python_steps

Type: task
Status: open
Blocked by: 06
Size: L

## Question

Bring these modules to ticket 01's standard, as the tickets before did theirs.

## Done when

- `tables.py`, `admin.py`, `upkeep.py`, `unchecked.py` and `python_steps.py` follow every rule
  in `docs/agents/standards.md`, and ticket 01's list has no line for them.
  `write_table_reference`, `create_table`, `check_key`, `_checked_partition`, `drop_partitions`,
  `move_to_own_folder` and `unchecked_derived` each read in one pass.
- No public name, Hive string, refusal message or report changes: the snapshot and the suite
  pass, tests edited only to follow a moved private name.
- The code-review skill has run, and its findings are fixed or answered here.
