# export_hive: each table's SQL in a file beside its notebook

Type: task
Status: resolved
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

## Answer

Built 2026-11-01 (b2c666c, merged as 3ba1651; review fixes 422ffc1, merged as 56ec7d6).

- `export_hive` in `sqlglot_composer/running.py`, public: with no argument, in a Table notebook,
  it writes `<db>__<table>.hql` beside the notebook, the steps it holds listed in its header in
  the order they are sent (`create()`, the dynamic-partitions setting and `seed()` when there is
  one, the Session settings, `write()`), each as `show_hive` shows it, `
` line endings, a
  Python step as comment lines; given a Statement, `<variable>.hql` beside the calling notebook
  or script. The same text when nothing changed; refused outside a Table notebook, and for a
  list, with four-part messages.
- The cell, after the lineage cell, in the saved_table and quality_checks Templates, the Table
  notebooks convert writes, and the Example projects' Table notebooks (`GAINED_BY_HAND`).
- How-tos 6 and 7, `docs/clean-branch-readme.md` (a generated .hql told apart from one the user
  writes for a Workflow), the Example projects' READMEs, Copilot files 06 and 08, and CHANGES.
  Copilot file 06 lost two checklist lines that repeated its own steps 2 and 3, to stay under
  8,000 characters with its new step.
- Tests: `tests/test_export_hive.py`.
- Code review (both axes): names made plain (`_notebooks_table_folder`, `pieces_of_the_file`,
  `_steps_held`), `_HIVE_FILE_END` private, one list of the Example projects' tables
  (`saved_and_converted_tables`), `newline="
"` on both writes; all fixed in 422ffc1.
- Beginner reader: [its report](../reports/01-beginner-reader.md); every stop but Hive's own
  `WITH ... INSERT` order fixed in 422ffc1, the costliest a refusal whose own loop fix wrote
  each Statement over the one before.
- D394, the version item this merge opened, closes with ticket 07's raise.

