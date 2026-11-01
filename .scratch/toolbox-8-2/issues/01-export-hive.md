# export_hive: each table's SQL in a file beside its notebook

Type: task
Status: open
Blocked by: -
Size: M

## Question

The user can't see at a glance the Hive a Table notebook's Python writes; `show_hive` prints it,
and nothing keeps it (map, "How SQL becomes tables today": Q1, Q5, Q10).

## Done when

- `export_hive()`, public, called with no argument in a Table notebook's cell, writes
  `<db>__<table>.hql` beside the notebook: `create()`, any `seed()`, the table's Session
  settings, then `write()`, in the order `run_tables` sends them, under a header saying it is
  generated from the notebook's logic and is edited there, not here. Its report names the file.
- `export_hive(statement)` writes one Statement's Hive, as `show_hive` shows it.
- The saved_table and quality_checks Templates, and the Table notebooks convert writes, gain the
  cell beside the lineage cell; the Example projects' Table notebooks gain it too, a hand change
  listed in `GAINED_BY_HAND` in `tests/test_upgrades.py`.
- Run twice with no change, it writes the same text; refused outside a Table notebook with a
  four-part message.
- How-to 6 (and whichever how-to shows the lineage cell) shows it; CHANGES.md's `## 8.2` names
  it; the Copilot files that list a Table notebook's cells name it.
