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

### Review (c91a5c3)

Code review: the Standards and Spec axes (`review-standards`, `review-spec`, on Sonnet), and
the drift review (D350). Fixed in the next commit:

- **Spec, the change written:** read from the notebook's code cells (`workflows.notebook_code`),
  so a call on several lines counts, and one commented out doesn't.
- **Standards:** `has_folder` for a bool; an `if` in place of a conditional loop iterable;
  `table_folder` and `conversion_folder` named apart in Promotion's checks; one way to run a
  Table notebook's logic, `_logic_namespace`, which `load` and `logic_loads` share; the test
  that repeated the graph test's zero is gone.
- **D350:** the location= you filled in goes with a prod copy to the new name rename= gives it.

Answered, not changed:

- **Spec, the check's own step and the preview's done function:** no file tells of either, as
  the Answer says; the check stays in the send's step, and the preview step is passed over
  once a later step is done.
- **Spec, "its notebook and how-to generated":** each Workflow's notebook is generated; its
  how-to is ticket 19's ("Each Workflow's how-to is generated from its step list").
- **Spec, logic_loads runs the user's logic from check():** that is "done when the Statement
  loads"; the logic cell builds Statements and sends nothing, as load refuses one that calls
  run_query or run_execute.
