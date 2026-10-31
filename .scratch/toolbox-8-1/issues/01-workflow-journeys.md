# End-to-end tests of each Workflow, and the hand edits each needs today

Type: task
Status: open
Blocked by: -
Size: L

## Question

The user (2026-10-31): "be sure to add tests that actually test the workflows". 8.0's
tests check one step at a time; nothing runs a Workflow from its start materials to its end goal
as the user does. Written first, before any 8.1 change, so each later ticket is measured by
them (map, "Tests that run the Workflows").

## Done when

- `tests/test_workflow_journeys.py` holds a journey per Workflow: it starts a Project, fills
  in the Workflow notebook's names cell as a user types it, and runs that notebook's code cells
  top to bottom, the notebook the Project ships, with `query` and `execute` the Example
  database's. Each ends by asserting its end goal from the Warehouse and the files: convert,
  each dev table written and compared and the Batch finished; promote, each prod table
  written; new_table, the dev table written; references, each Table reference and the
  Reference sheet; change_a_saved_table, the change sent and logged; upgrade, no mark left.
- A journey for the user's own case: one long script, CTEs, CREATE statements, a staging table
  read later and DROPped, a FROM with several INSERTs, into Databases the user can't write to,
  through convert and promote to prod tables.
- Each hand edit a journey needs today, a file opened and changed or a box ticked, is a named
  step in it, and listed, by journey and step, in a known-fiddling list in the test file. A
  test fails on a hand edit the list doesn't hold, and on one it holds that no journey needs,
  so the list only shrinks, as `tests/repo/known_breaks.py` does.
- The list's count per Workflow is recorded here, as today's baseline, beside 8.0's fiddling
  count from `tools/workflow_graph.py`.
- The journeys run in the whole suite, within its time; a journey that is slow says why.
- **One source of steps**, a repo test: for each Workflow, its steps, in order, are the same in
  `workflows.py`, its notebook's cells, `docs/workflows.md`, the README's charts and lists,
  how-to 29 and Copilot file 13. A Workflow step's call that a hand-written Copilot file (07,
  11, 12, 06, 02) or how-to quotes is a call of one of today's steps, and a retired name, such
  as `finish_conversion`, appears in none (`tests/repo/test_no_retired_name.py` covers the
  Copilot files' sources and the generated files both).
- Run on 8.0's docs and Copilot files now, it passes, or each place it finds is fixed in this
  ticket: the listed steps are correct before 8.1 changes them.
