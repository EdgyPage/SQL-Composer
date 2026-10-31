# 8.0: the Upgrade step and the raise

Type: task
Status: resolved
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
- (left, from ticket 14) a 7.2 Project's open Conversion folders, in admin/conversions/,
  which no finish_conversion can finish now: the Upgrade converts each again as a batch of one,
  or marks it, and its user scripts that call finish_conversion get an `# UPGRADE 8.0:` mark.
- (left) CHANGES.md's `## 8.0` is complete, with "To update from 7.2" holding every later
  ticket's changes.
- CLAUDE.md names 8.0 and the admin layout. CI passes; the export is the user's call.

## Answer (2026-10-31)

- An open 7.2 Conversion, `admin/conversions/<name>/`, can't be converted again by the Upgrade:
  a batch needs `DEV`, which the Upgrade only adds, unfilled, and the user may have changed the
  Conversion's notebook. So the 8.0 step marks it: it puts the Hive beside
  `admin/workflows/convert/convert.ipynb` as `<name>.hql`, archives the whole 7.2 folder into
  `admin/removed/` (the notebook with the user's changes too), takes `admin/conversions/` out,
  and marks the convert notebook's names cell, `# UPGRADE 8.0: convert <name> again, as a
  batch: NAME = "<name>", FILES = ["<name>.hql"], ...`. The registry's `conversion_folder` row
  keeps its name, which the batch, given the same NAME, takes over.
- Each line of the user's code that calls `finish_conversion` is marked: `upgrades.calls_to`
  parses each .py file and code cell, so a docstring, comment or text cell that names it (as
  the 7.2 Intermediate project's finished table does) is not marked.
- `GAINED_BY_HAND`: `warehouse.py` is out (the step rewrites a 7.2 warehouse.py). The starter's
  `README.md` stays: 8.0's README text is written by hand, and an Upgrade never rewrites a
  Project's README, which is the user's.
- CHANGES.md's `## 8.0` opens with what 8.0 is, and its "To update from 7.2" adds filling in
  `DEV` and `PROD` and the open Conversions. CLAUDE.md names 8.0's admin layout.

### After the review (2026-10-31)

- Code review: the Standards axis found no hard breach; its points taken: one reader of a
  file's texts, `_texts_of`, for marks_in and calls_to; the convert folder named once,
  `CONVERT_FOLDER`; `statement`, `tables_read` and `named_by_others` in place of `query`,
  `read` and `named`; CONTEXT.md reflowed; CLAUDE.md's layout in a section of its own. The Spec
  axis: a cell with a %magic or !command is now read with those lines blank, so its call is
  still marked; a Conversion folder with no original.hql gets a mark that names no FILES; the
  clash check moved out of `dev_names` into its own refusal (below). Left as is: the
  checklist lists one file's marks from its last line up, as they are made; a call after a
  backslash continuation (rare).
- The step marks each name in admin/databases.py still `<...>`, the ticket's "its names marked
  for the user", which ticket 12 had left out; how-to 28 shows filling them in.
- Beginner reader: [20-beginner-reader.md](../reports/20-beginner-reader.md). Its stops are
  answered there, each with what was done.
