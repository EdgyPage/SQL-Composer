# 8.0: the Upgrade step and the raise

Type: task
Status: open
Blocked by: 19
Size: M

## Question

The user (2026-10-30): "version 8". Every raise ships an Upgrade step and freezes the Example
projects as the version before left them.

## Done when

Ticket 12 raised the version to 8.0 and wrote `to_8_0` (its Answer says why): the raise, the
notebooks replaced and archived, `databases.py` and `sent.csv`, the warehouse.py rule,
`GAINED_BY_HAND` and `tests/upgrade_from/7.2/` are done. What is left is marked (left) below.

- `sqlglot_composer/version.txt` says 8.0.
- `upgrades.py`'s step from 7.2 to 8.0: writes `admin/databases.py` (its names marked for the
  user) and `admin/sent.csv`; (left) moves `admin/conversions/` into `admin/workflows/convert/`
  if ticket 13 moves it, each unfinished Conversion kept as an instance; replaces the one-action admin notebooks with the
  agnostic ones and the Workflow notebooks, archiving each first; (left) marks each user script
  that calls `finish_conversion` with `# UPGRADE 8.0:`, if ticket 14 changes it.
- The 8.0 step replaces a Project's warehouse.py that still holds 7.2's text, untouched, with
  8.0's, which holds `conn` (ticket 21); one the user changed is left as it is. The
  `warehouse.py` and starter `README.md` entries ticket 21 added to `GAINED_BY_HAND` in
  `tests/test_upgrades.py` come out.
- `tests/upgrade_from/7.2/` freezes the Example projects as 7.2 left them, without Lineage pages;
  `tests/test_upgrades.py` passes.
- (left) CHANGES.md's `## 8.0` is complete, with "To update from 7.2" holding every later
  ticket's changes.
- CLAUDE.md names 8.0 and the admin layout. CI passes; the export is the user's call.
