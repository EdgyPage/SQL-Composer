# 8.1: the Upgrade step and the raise

Type: task
Status: resolved
Blocked by: 12
Size: M

## Question

The user named 8.1 (2026-10-31). Every raise ships an Upgrade step and freezes the Example
projects as the version before left them.

## Done when

- `sqlglot_composer/version.txt` says 8.1, and `upgrades.py`'s `to_8_1` gives a Project's
  Workflow notebooks their decisions cells, keeping each as it was; an 8.0 `checklist.md` with
  boxes ticked by hand carries each answer it can into the cell.
- `tests/upgrade_from/8.0/` freezes the Example projects as 8.0 left them, without Lineage
  pages; `tests/test_upgrades.py` passes.
- CHANGES.md's `## 8.1` is complete, its "To update from 8.0" holding every ticket's changes;
  CLAUDE.md names 8.1.
- The known-fiddling list holds only upgrade's marks. CI passes; the export is the user's
  call.

## Answer

Built 2026-10-31, before ticket 12's read of the docs, so 12 reads them at 8.1.

- `sqlglot_composer/version.txt` says `sqlglot Composer 8.1`; the version the user named.
- **`upgrades.to_8_1`:** writes each Workflow notebook again, kept in admin/removed/ first:
  each name its names cell gave kept (`_names_cell_kept`), each UPGRADE mark an earlier step
  left above a name kept above it (`_marks_above`: an Upgrade from 7.2 runs 8.0's step, which
  marks the convert notebook, then 8.1's), and each step cell the user writes in kept, one
  whose call holds a `...` to fill in, such as change_a_saved_table's Admin statement
  (`_step_cells_written`). Each Template still as 8.0 wrote it is written again, one the user
  changed marked (moved here from the 8.0 step, which never shipped); each converted table's
  checklist.md is written again as the view of its Decisions (`project.write_checklists_
  again`), no boxes. Settled: an 8.0 checklist's ticked boxes carry nothing into the decisions
  cell, since a box was ticked once its answer was in the Table reference, which keeps it.
- **`tests/upgrade_from/8.0/`** freezes both Example projects as 8.0 left them (at 39206c5,
  the last commit before 8.1's code), without Lineage pages. `GAINED_BY_HAND` names the files
  8.1 changed by hand in them.
- **The upgrade journey** starts from 8.0's Starter with a Template the user changed, which
  8.1's step marks; KNOWN_FIDDLING keeps upgrade's marks, and new_table's logic for a table
  started by hand, what the user writes.
- CHANGES.md's `## 8.1` has its opening and "To update from 8.0"; how-to 28, the upgrade
  and version docstrings say 8.1.
- **Code review:** Standards: `workflow: object` hints (now `Workflow`, imported for hints
  alone), a names cell's line written in two places (now `workflows.input_line`), the step
  heading parsed twice (now `workflows.step_name_of`), the STEPS comment drifted onto
  `to_8_1` (moved back), plainer names, the checklist heading read back by a literal (now
  `CHECKLIST_HEADING`). Spec: a names cell starting with an UPGRADE mark gave no names to
  `given_inputs`, so an Upgrade from 7.2 reset what the user typed under the convert
  notebook's mark (now the cell is found by any line; a test holds it); the checklists written
  directly (now through `upgrade.rewrite`, kept in admin/removed/ first). Left, settled: a box
  ticked in 8.0 carries nothing into the decisions cell, since its answer is in the Table
  reference already; a cell the user changed other than the names cell and a step cell they
  write in is kept only in admin/removed/; KNOWN_FIDDLING keeps new_table's logic for a table
  started by hand and change_a_saved_table's Admin statement, what the user writes (8.1's Q15).
- **Beginner reader:** CHANGES' 8.1 and how-to 28 are read with ticket 12's docs.
