# check() and an unrecorded change

Type: task
Status: resolved
Blocked by: 02
Size: S

## Question

A logic cell edited and written with `write()`, but never exported with `export_hive()`,
leaves the Lineage state behind. `check()` says so, and records nothing (Q21).

## Done when

- **`project.check()`** works out the Project's columns (ticket 01) and compares them with the
  last recording: "N columns' logic differs from the last recording: mart.x, mart.y. Run cell
  5 of each one's Table notebook, or project.record_lineage_state() in admin/lineage.ipynb."
- With no recording yet, it says to make the first.
- It writes nothing, the CSV included; a test holds it.
- A table that doesn't build is named as `check()` names it already, once.

## Answer

Built 2026-11-17, from dev's 67420e18 (tickets 01 and 02), beside tickets 03 and 05.

- **`project.check()`** gains, after its blocking lines and before what blocks nothing, the
  Lineage state's lines, from `_lineage_state_lines` in `project.py`, which imports
  `effective_logic` and `lineage_state` where it runs, the import at the top being circular:
  - with no recording yet, in a Project with a Table folder, Scheduled run or Table reference
    in force and `admin/lineage.ipynb` there (`LINEAGE_NOTEBOOK`, which ticket 07 writes and
    the Upgrade adds), "No Lineage state yet: record the first with
    project.record_lineage_state(), in admin/lineage.ipynb." (only the CSV is read: no logic
    is worked out). Without the notebook the Project is from before 8.8, which check()'s
    version line names already; asking for a recording there would also have put the line in
    every README step, how-to and Example project that checks a Project until ticket 03's
    recordings and ticket 07's notebook land, then taken it out again;
  - with one, `lineage_state.unrecorded_changes(root, effective_logic.project_logic(root))`,
    and when it finds any, "The Lineage state is behind: 3 columns' logic differs from its
    last recording, in mart.job_day_facts and mart.team_days. Record it: run cell 5,
    export_hive(), of the Table notebook you changed, or project.record_lineage_state(), in
    admin/lineage.ipynb.";
  - its docstring says so. It writes nothing, the CSV included.
- **`lineage_state.unrecorded_changes(root, logic)`**, new: what `record` would add a row for,
  of the columns, writing nothing; `record` and it share `_changes_since`, so check() and a
  recording never disagree. Building blocks aren't counted: a block's change alone, which
  changes no column, isn't "logic differs".
- **A table that doesn't build is named once**, where check() names it already: a fix to
  ticket 01's `project_logic`, which made a Table folder that didn't build a Table-reference
  root, so its columns read as changed (and `record` would have written them so).
- **Cost**, measured on the Intermediate Example project (13 tables, 56 columns): check()
  0.14 s without these lines, 0.24 s with a recording to compare, about 0.1 s more; with no
  recording yet, no more than before. No Workflow calls check(), so none is slower.
- **Tests:** `tests/test_check_unrecorded.py`, 5: the first recording asked for once
  `admin/lineage.ipynb` is there, and not before, nothing said
  of a state up to date, a Building block changed naming its tables and recording nothing,
  then nothing once recorded, a table that doesn't build left out of the line, and a Project
  with nothing to record saying nothing of it.
- **A test leak fixed:** the `intermediate` fixtures of `tests/test_effective_logic.py` and
  `tests/test_lineage_state.py` put back the modules they deleted but left those the copy
  imported, such as `references.ops`, for the next test on the worker, which failed
  `test_two_tables_of_one_database_by_one_name_leave_the_second_out`; each now calls
  `conftest.forget_the_projects_modules()` after, as this ticket's does.
- The whole suite passed, its snapshot written again; `docs/main/examples.html` regenerated
  for check()'s docstring.

## Comments

**Code review, 2026-11-17**, of tickets 01 to 06 together (3daf6b09..973594c2), its two axes
on Sonnet, recorded in the ledger as round toolbox-8-8-01-06. Fixed in 3d4a9bac:
- Standards: a whole-table read's expansion was written twice (`lineage_state._each_column`,
  `lineage_difference._reads_of`), now `effective_logic.each_column` and `column_key`;
  `CHANGES_AT_THE_COLUMN` repeated `ROOT_CHANGES`, now gone; `_recorded`, a vague name, is
  `_unrecorded_lines` and `_report_once_recorded`, which builds the call the five actions on
  names each built; a table's change words and box kind come from one map each.
- Spec: `building_blocks/prod/` wasn't hashed, so a prod copy's own change named no block;
  it is now, as `prod/<name>`.

Answered, no change:
- `because` names every changed column up the chain, nearest first, not only the farthest:
  each is a column the inherited change comes from, which the difference's chains need.
- "No Lineage state yet" waits for `admin/lineage.ipynb`: ticket 07 writes it.
- Recordings in one second: `_recorded_at` gives every recording, `export_hive()`'s too, its
  own second. A bumped time can be a few seconds after the clock, so a write in those seconds
  reads as before the change: a few seconds' slack, kept.
- An opaque step's readers show `inherited`: their own logic is unchanged, as Q3 and the
  Inherited change's definition say.
- `since=` before the first recording starting from it, and Building block rows in the one CSV,
  are the ticket changes each Answer records.
- The smells left: the `before` and `rows` pair (a `Recording` type), `record` returning
  text that `record_lineage_state` compares, the Middle Men `deciding_boxes` and `_columns`, and
  `difference(call=...)`'s default. Judgement calls, left for a refactor with no version raise.
