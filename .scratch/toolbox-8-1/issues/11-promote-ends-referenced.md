# Promote ends referenced: the Reference sheet and the Database modules

Type: task
Status: resolved
Blocked by: 01
Size: S

## Question

A promoted table is referenced only once the user refreshes the Reference sheet by hand
(map, "Referenced and maintained": Q19).

## Done when

- promote's last step, a file step, refreshes the Reference sheet and the Database modules
  for the prod tables, and `do_next()` and the runner run it.
- Its journeys show it (`tests/test_workflow_journeys.py`, ticket 01): the promote journeys end
  with each prod table in the Reference sheet.

## Answer

Built 2026-10-31.

- promote's step 7, a file step, `project.refresh_reference_sheet(project.promoted_tables(TABLES))`
  (`workflows.refresh_the_prod_sheet`), done when the Reference sheet was written after each
  prod copy's Table reference (`workflows.prod_sheet_is_fresh`). `do_next()` and the runner run
  it; promote's end artifacts add "each in the Reference sheet".
- The promote journeys, both ways, end with each prod table in the Reference sheet and its
  Database module.
- Found on the way: a dry run ran this step for real, after the creates and writes it only
  showed, and its fresh sheet then said every step before it was done, so the real run sent
  nothing. A dry run now names a file step after one that would send, "would run: ...", and
  runs none (`project._step_lines`, `Calls.shown`); the promote journey holds it.
- Copilot file 13, how-to 29 and the Example projects' promote notebooks list the step,
  written again from the Workflow; the one-source test held each.
- Code review: Standards: `Calls.shown` named like the file kinds' `shown` and
  `would_send` no verb (now `hive_lines_said`, `say_would_send` and `would_have_sent`), a
  table name split by hand in the journey (now `split_table_name`), `_step_lines` read in one
  pass. Spec: `prod_sheet_is_fresh` said yes before any prod copy existed whenever a Reference
  sheet did, which would have read a new promote as finished (now `reference_sheet_is_fresh`
  says no for no tables; `test_run_workflow` holds it); one `Calls` for every batch, so one
  batch's dry run made the next one's file steps only named (now one per instance); a
  docstring line too long.
- Beginner reader: [11-beginner-reader.md](../reports/11-beginner-reader.md).
