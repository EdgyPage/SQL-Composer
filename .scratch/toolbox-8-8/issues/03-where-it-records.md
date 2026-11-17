# Where it records

Type: task
Status: resolved
Blocked by: 02
Size: M

## Question

"Every time I change a table or reference, a lineage file would have to be generated." The
Toolbox can't see a logic cell edited in Jupyter, only the calls it is given, so it records at
each call that changes a table or Table reference (Q5, Q14).

## Done when

- **Each Project action that changes a table or Table reference** records at its end, its
  `recorded_by` naming the call: making or removing a Table folder or Scheduled run, adding
  Table references, `convert`, `promote`, `refresh_reference_sheet`, and the
  `change_a_saved_table` Workflow's last step. A Project action that takes many names records
  once, after the last.
- **A Table notebook's `export_hive()`** (cell 5) records, `recorded_by` naming the notebook,
  and prints ticket 02's line; cell 5's comment in `project_templates.py` says so. Cell 4's
  `export_lineage` doesn't record (Q14).
- **Never a Scheduled run**: `build_run` and `built.run` record nothing; a test holds it.
- A recording that fails, such as a CSV left open in Excel, never fails the action it ends: the
  action's report says what wasn't recorded and the cell that records.
- The Example projects' notebooks are regenerated with cell 5's new comment.

## Answer

Built 2026-11-17, on dev's 67420e18 (tickets 01 and 02 merged).

- **`project.record_after_a_change(root, recorded_by) -> list[str]`**, beside
  `record_lineage_state`, records the whole Project (`effective_logic.project_logic`, then
  `lineage_state.record`), both imported where it runs, since `effective_logic` imports from
  `project`. Whatever stops the recording is caught: it gives one line,
  "Lineage state not recorded: <error>: <what happened>. Record it with
  project.record_lineage_state(), in admin/lineage.ipynb." (`NOT_RECORDED`), and what called it
  stays done.
- **Each Project action that changes a table or Table reference** records once at its end,
  after its last name, through `_recorded(report, root, recorded_by)`, which keeps the report as
  it was and adds only that failure line: an action prints nothing more when the recording
  works, so no action's report or docstring changed. Each `recorded_by`, the call as written:
  - `project.new_table("mart.x")`, or `project.new_table(["mart.x", "mart.y"])`;
  - `project.remove_table(...)`, `project.new_scheduled_run(...)`,
    `project.remove_scheduled_run(...)`, the same way;
  - `project.add_references([...], query=...)`, which records before it refuses the tables it
    skipped, so what it wrote is recorded;
  - `project.convert("<batch>", ...)`, at the end of each batch;
  - `project.promote(...)`;
  - `project.refresh_reference_sheet()`, or with its names; its docstring says so, and
    `admin/check_references.ipynb`'s text, whose first cell refreshes the sheet.
  - Not `register`, `new_block` or `remove_block`, which the ticket doesn't name: the next
    recording sees what they did. A list of names a refusal stops partway isn't recorded; the
    next recording, or `check()` (ticket 04), catches it.
- **A Table notebook's `export_hive()`** (cell 5) records as
  `tables/<db>__<table>/<db>__<table>.ipynb export_hive()` and prints ticket 02's line after
  what it wrote, such as "Lineage state: 4 columns changed (2 own, 2 inherited):
  project.export_lineage_difference() shows them." `export_hive(statement)` records nothing.
  Its docstring says so; cell 5's comment, in `project_templates.py`, now reads "# 5. Its Hive:
  <NAME>.hql beside this notebook, from the logic as last saved, then the / #    Project's
  Lineage state recorded: run it after each change to the logic".
- **`change_a_saved_table`'s last step** is `run_execute(change, execute)` then
  `project.record_lineage_state()`, its action text saying so; the Workflows page, the README's
  chart, how-to 29 and Copilot file 14 are written again from it.
- **Never a Scheduled run**: `build_run` and `built.run` call nothing that records;
  `test_a_scheduled_run_never_records` builds and runs one with `lineage_state.record` made to
  fail if called.
- **The clock** (a decision): `lineage_state._recorded_at` gives a recording the time now, or a
  second after the file's last recording when now isn't later, so two recordings in one second,
  as the Example projects' pinned clock makes every one, each have their own `recorded_at`, and
  the file's times only grow, as `columns_at` replays them. Nothing else's time changes: the
  Admin log keeps the pinned time. The Example projects' states run 06:00:00, 06:00:01, ... .
- **The Example projects** are written again: each Table notebook's cell 5, the Templates,
  `check_references.ipynb`, `change_a_saved_table.ipynb`, and a new
  `admin/lineage/lineage_state.csv`, a recording for each action the tool runs (10 in the
  intermediate project, 6 in the starter). The pages built from them, the gallery, the how-to
  page (how-to 06 shows the new line) and the Copilot files are written again.
- **For ticket 10:** `tests/test_upgrades.py`'s `AWAITING_ITS_STEP` leaves out, until 8.8's
  Upgrade step writes them, `admin/check_references.ipynb`, the two Templates,
  `admin/workflows/change_a_saved_table/` and each Table notebook (cell 5's comment). The step
  needs an 8.7 entry for `saved_table` and `quality_checks` (as `TEMPLATES_BEFORE_8_6`), the two
  admin notebooks written again, and each Table notebook's cell 5 comment rewritten or left; then
  `AWAITING_ITS_STEP` empties.
- **Tests:** `tests/test_where_it_records.py`, 12: new_table records naming its call and prints
  nothing more; two recordings in one second each their own time; a list of names records once;
  remove_table records removed; refresh_reference_sheet records; a recording that fails leaves
  the action done and says so; export_hive in a Table notebook records and prints; given a
  Statement it doesn't; a Scheduled run never records; change_a_saved_table's last step; cell 5's
  comment. `test_an_action_on_several_names_reads_the_registry_once` counts the actions' own
  reads, the recording's patched out; `test_export_hive` and `test_hivevars` compare what was
  written, before the Lineage state's line.
