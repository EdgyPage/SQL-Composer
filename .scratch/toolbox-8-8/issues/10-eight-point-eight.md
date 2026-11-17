# 8.8: the Upgrade step and the raise

Type: task
Status: resolved
Blocked by: 01, 02, 03, 04, 05, 06, 07, 08, 09
Size: M

## Question

The version the user named, and the Upgrade step every raise ships (Q17).

## Done when

- **`upgrades.to_8_8`, in `STEPS`:**
  - writes `admin/lineage.ipynb`, as `project.start()` does, leaving one the user made alone;
  - makes the Project's first recording, `recorded_by` the Upgrade, every column `first`;
    from 8.9 on, the recording an Upgrade makes marks each change `toolbox` (ticket 02, ADR
    0015);
  - touches nothing under `scheduled_runs/<name>/`, which
    `test_an_upgrade_keeps_every_scheduled_run_file_at_its_path` holds;
  - loses none of the user's code, and changes nothing in the warehouse.
- **The Example projects are frozen at 8.7** in `tests/upgrade_from/8.7/`, without their
  Lineage pages, and `tests/test_upgrades.py` passes.
- `sqlglot_composer/version.txt` reads 8.8.
- **CHANGES.md's `## 8.8`** has "What's new" and "To update from 8.7".

## Answer

Partly built 2026-11-17, from dev's 973594c2 (tickets 01 to 06), beside ticket 07: all but
`admin/lineage.ipynb`, which ticket 07 makes.

- **`upgrades.to_8_8`, in `STEPS`:**
  - each Table notebook's export_hive() cell still as 8.7's Templates wrote it
    (`HIVE_CELL_8_7`) gets 8.8's comment (`HIVE_CELL_8_8`), written in its cell alone
    (`rewrite_cells`); a comment you changed is left, as the cell records all the same; a Table
    notebook with no export_hive() cell is marked (`NO_HIVE_CELL_8_8`) on its first code cell
    that isn't its logic cell, never above `# logic`, by which project.load finds the logic;
  - each Template still as 8.7 wrote it (`TEMPLATES_BEFORE_8_8`, `saved_table` and
    `quality_checks` by hash) is written again, one you changed marked (`TEMPLATE_MARK_8_8`);
  - `admin/check_references.ipynb`'s text cell is 8.8's, its code cells as they are;
  - the `change_a_saved_table` Workflow's notebook is written again
    (`_write_workflow_notebook_again`, `_write_workflow_notebooks_again` for one Workflow),
    each name and step cell of yours kept, its last step recording;
  - `upgrade.add_what_start_makes()`, which adds what project.start() makes that the Project
    lacks, writing over nothing;
  - the records of promote and convert rehashed, as 8.6 and 8.7 do;
  - last, the first recording: `project.record_after_a_change(root, "project.upgrade() to 8.8",
    by_upgrade=True)` (`RECORDED_BY_8_8`; `record_after_a_change` gains `by_upgrade=`), every
    column `first`, its line in `admin/upgrade_8.8.md`'s "Done for you". A recording that fails
    leaves the step done, its checklist saying so.
  - Nothing under `scheduled_runs/<name>/` is touched; nothing is sent.
- **`admin/lineage.ipynb` (ticket 07):** once `project.start()` writes it, as an admin notebook
  in `ADMIN_NOTEBOOKS` or among what start() makes, `add_what_start_makes()` in `to_8_8` adds
  it to an upgraded Project, leaving one you made alone; no line of `to_8_8` changes. If 07
  makes it some other way, it goes in `to_8_8` before `_record_the_first_lineage_state`, as
  `upgrade.add(...)`. Then this ticket resolves.
- **The freeze:** `tests/upgrade_from/8.7/`, the Example projects at 3daf6b09 (8.7, before any
  8.8 code), 114 files, without their lineage folders.
- **`tests/test_upgrades.py`:** `AWAITING_ITS_STEP` is empty; the 7.1 test names 8.7's step;
  the test that 8.7 loses no line runs 8.7's step alone, later steps taken out of `STEPS` for
  it, since 8.8 writes lines of its own; and four new tests: the first recording as the
  Upgrade's, cell 5's comment written where 8.7 wrote it and left where you changed it, a Table
  notebook with no export_hive() marked never above its logic, a Template written again and
  one you changed marked.
- **The raise:** `version.txt` reads 8.8; CHANGES.md's `## 8.8` ("To update from 8.7" and
  "What's new", `admin/lineage.ipynb` among it); the README's Update names 8.8's Upgrade; the
  Example projects, the pages and the Copilot files written again at 8.8.
- **Resolved 2026-11-17**, once merged with ticket 07: `admin/lineage.ipynb` is one of
  `ADMIN_NOTEBOOKS`, so `add_what_start_makes()` adds it to an upgraded Project, as this
  Answer foresaw, with no line of `to_8_8` changed;
  `test_8_8_adds_admin_lineage_notebook_and_leaves_one_you_made` holds it, and that one the user
  made is left.

## Comments

**Code review, 2026-11-17**, of tickets 07 and 10 together (ed012145..de42dd88), its two axes
on Sonnet, round toolbox-8-8-07-10 in the ledger. Spec: nothing missing or wrong; its scope
notes (check()'s first-recording question waiting for a column, ticket 03's carried-forward
files in `to_8_8`) are what each Answer records. Standards, no hard violation; fixed:
- `_write_workflow_notebook_again` copied `_write_workflow_notebooks_again`'s body: both now
  call `_workflow_notebook_now`, and the one for a single Workflow is
  `_write_one_workflow_notebook_again`;
- `first`, a list of every code cell but the logic cell, is `not_logic`;
- `_record_the_first_lineage_state`'s docstring said "from 8.9 on" for what it does now.

Left: `by_upgrade=` beside `recorded_by` (ADR 0015 keeps the Toolbox's rewrite apart from the
call that records, so the flag stays), `upgrade.changed.append` in place of a method, the
`[0]` text cell of `check_references`, and the tests' copy helpers, judgement calls.
