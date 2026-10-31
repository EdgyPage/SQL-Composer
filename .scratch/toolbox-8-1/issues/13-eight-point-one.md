# 8.1: the Upgrade step and the raise

Type: task
Status: open
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
