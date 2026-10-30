# 8.0: the Upgrade step and the raise

Type: task
Status: open
Blocked by: 19
Size: M

## Question

The user (2026-10-30): "version 8". Every raise ships an Upgrade step and freezes the Example
projects as the version before left them.

## Done when

- `sqlglot_composer/version.txt` says 8.0.
- `upgrades.py`'s step from 7.2 to 8.0: writes `admin/databases.py` (its names marked for the
  user) and `admin/sent.csv`; moves `admin/conversions/` into `admin/workflows/convert/`, each
  unfinished Conversion kept as an instance; replaces the one-action admin notebooks with the
  agnostic ones and the Workflow notebooks, archiving each first; marks each user script that
  calls `finish_conversion` with `# UPGRADE 8.0:`.
- `tests/upgrade_from/7.2/` freezes the Example projects as 7.2 left them, without Lineage pages;
  `tests/test_upgrades.py` passes.
- CHANGES.md's `## 8.0` is complete, with "To update from 7.2".
- CLAUDE.md names 8.0 and the admin layout. CI passes; the export is the user's call.
