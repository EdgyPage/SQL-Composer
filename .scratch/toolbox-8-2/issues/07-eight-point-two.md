# 8.2: the docs, the Upgrade step and the raise

Type: task
Status: resolved
Blocked by: 06
Size: M

## Question

8.2 ships `export_hive` and what the rounds changed (map: the user named the version 8.2).

## Done when

- `sqlglot_composer/version.txt` says 8.2, the version the user named.
- `upgrades.STEPS` has 8.2's step: each Table notebook without the export_hive cell gains it,
  under an UPGRADE mark where the notebook was changed by hand; the Example projects are frozen
  as 8.1 left them, without their Lineage pages, in `tests/upgrade_from/8.1/`.
- CHANGES.md's `## 8.2` opens with what changed and how to update from 8.1.
- CLAUDE.md names 8.2.
- The Copilot held-out evaluation runs on every Copilot file 8.2 changed, and the Excel one if
  files 11 or 12 changed; each score is recorded.

## Found since

- Ticket 11: a Table notebook and checklist.md a new_table table wrote before 8.2 send its
  Decisions to convert's notebook; the Upgrade step writes them to name new_table's.
- Ticket 14: the convert notebook's names cell gains RENAME, which its step's call reads: the
  Upgrade step writes each Workflow notebook again, keeping each name given, as `to_8_1` does.

## Answer

`version.txt` says 8.2. `upgrades.to_8_2`:
- puts the Hive cell, `export_hive()`, after each Table notebook's lineage cell (any cell
  calling `export_lineage(`), its checklist line saying to run it, and marks a notebook with no
  lineage cell;
- writes each Workflow notebook again through `_write_workflow_notebooks_again`, which 8.1's
  step now shares, each name given kept, so convert's names cell gains RENAME;
- writes again each Template still as 8.1 wrote it (`TEMPLATES_BEFORE_8_2`), marking one you
  changed, through `_write_templates_again`, which now takes each version's hashes and mark;
- for each table a batch new_table made holds (its record's `made_for`), writes its notebook's
  text cell and compare cell's opening as 8.2 writes them, through
  `project.converted_notebook_text` and `project.compare_ahead`, and its checklist.md naming
  new_table's notebook.

`tests/upgrade_from/8.1/` freezes both Example projects as dev 204387d1, which 8.1 was exported
from, left them, without Lineage pages; `GAINED_BY_HAND` now lists only what 8.2 gained by hand.
`test_an_upgraded_notebooks_hive_cell_writes_the_example_projects_hive` runs each upgraded
notebook's Project, logic and Hive cells through `tools/notebook_runner.py` and holds the file
written to the Example project's. CHANGES' `## 8.2` opens with what changed and To update from
8.1; CLAUDE.md names 8.2 already. How-to 28, the upgrade docstring's doctest and
`__init__`'s doctest say 8.2; H2's key wants 8.2 in project_version.txt.

The Copilot held-out evaluation, haiku, arm C, on every file 8.2 changed: 06 (T18) and 08
(T24), 1 of 1 each; 13 (T38, T39) 2 of 2; 14 (T36) 1 of 1; the Excel files 11 and 12, 85% of
39, against 97% on 8.1's files, none of its six failures on the one bullet 8.2 changed: each is
recorded in `.scratch/copilot-eval/results.md` with its reasons. D394 closes here, and so does
D403 (4bdaf41's kept-whole bullet gave the example ticket 16 now converts).

## Review

- Standards: no hard finding. The Workflow-notebook loop 8.1's and 8.2's steps both ran is
  `_write_workflow_notebooks_again`; the checklist and notebook rewrite use one pair of path
  constants; `_tables_made_by_new_table` and `rewritten` are named for what they hold. The
  Template hashes and mark stay two plain arguments.
- Spec: files 06 and 08, changed by ticket 01, are scored on held-out; a test holds a name
  given in 8.1's convert notebook kept beside the new RENAME; a new_table table's text cell is
  written as 8.2 writes it, not only its path, and its test writes 8.1's text out as 8.1 wrote
  it, not from the step's own replacements; a batch record that isn't JSON is passed over. A
  notebook is marked only when it has no lineage cell: one changed by hand in other ways gets
  the cell after its lineage cell, as the Upgrade can place it.
- Beginner reader: `.scratch/toolbox-8-2/reports/07-beginner-reader.md`; its three costliest
  stops are fixed (the checklist says to run the Hive cell; the no-lineage mark says where the
  cell goes; the Template mark says where a fresh Template is).
