# The other four Workflows with no fiddling

Type: task
Status: resolved
Blocked by: 17
Size: M

## Question

new_table, references, upgrade and change_a_saved_table, each with the steps grilled on
2026-10-30, brought to no fiddling edge.

## Done when

- **new_table**: `new_table(names)`; the logic, the user's step, done when the Statement loads;
  `run_tables` in dev; `preview`.
- **references**: `add_references(names, query=query)`; the TODO lines, the user's step, done
  when none is left; `refresh_reference_sheet()`.
- **upgrade**: `upgrade()`; each `# UPGRADE` box, the user's.
- **change_a_saved_table**: the Admin statement chosen; `show_hive`, which sends nothing;
  `run_execute`, a permission; the check it names.
- Each is in its step list, its notebook and how-to generated; the graph shows no fiddling edge
  in any of the six Workflows, and the test that held the baseline now holds zero.

## Answer

Built 2026-10-31. No step of the six Workflows is fiddling, and the graph test holds zero for
each (tickets 13 to 17 brought convert and promote there).

- **new_table:** `project.new_table(TABLES)`, a file step; fill in each Table reference, a
  decision, done when it holds no TODO line or placeholder; write each table's logic, a
  decision, done once its logic runs and its write() builds its Statement
  (`workflows.every_logic_loads`, through `project.logic_loads`, as
  `project.load(table).write()` does); check each table's rows with `preview()`, a
  permission, before it writes; create and write each in dev. Settled here: the notebook's
  text cells name a Template's placeholders to say what each was, so a placeholder anywhere
  in the notebook no longer counts as one left; the logic loading is what counts. Promotion's
  refusal reads it the same way.
- **The preview step** has no done function: a `run_query` isn't recorded in admin/sent.csv,
  which records what changes the warehouse, so no file tells of it. Once a later step is done
  it is passed over, as the Workflows already do for a step the files can't tell of.
- **references:** `add_references(TABLES, query=query)`; the TODO lines, done when none is
  left; `refresh_reference_sheet(TABLES)`. As it was.
- **upgrade:** `upgrade()`; each `# UPGRADE` mark, done when none is left. As it was.
- **change_a_saved_table:** write the Admin statement, now done once the change cell names one
  with its arguments (`workflows.change_written`); print its Hive with show_hive, which sends
  nothing; send it and run the check its report names, a permission, done when admin/sent.csv
  records it. The check stays in the send's step: no file tells of a check alone, so a step of
  its own would never be done, and the Workflow never end.
- The Workflow notebooks import `run_query`, for the preview step.
- Tests: `tests/test_workflow_steps.py`.
- D347, D348 and D349 fixed here: a prod Table reference is held even when the prod copy has no
  Table folder, and one deleted is reported; promoting under a new name archives the prod copy
  under the old one and marks its registry rows removed; CHANGES's Promotion bullet names what
  ticket 17's review commit added.
