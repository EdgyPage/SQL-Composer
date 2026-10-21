# Table references for Projects

Type: task
Status: resolved
Blocked by: 01, 03
Size: M

## Question

Map Notes, "write_table_reference", "Aliases". `write_table_reference(name, send, folder=None)`
writes `<db>__<table>.py` (no `t_` rule), with a commented Aliases heading and examples below
the `Table(...)`, and fills `Table`'s new optional `descriptions={column: text}` from DESCRIBE's
comments. `Table` refuses a `descriptions` key that isn't one of its columns.

## Done when

- Generated files import as `from references.<db>__<table> import <table>`.
- The pytest runs pass, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).

## Answer

Built 2026-10-21 on branch `toolbox-6/05-table-references`.

- `write_table_reference(name, send, folder=None)` writes `<db>__<table>.py` into `folder`
  (which must be there already) or the folder you're working in, and refuses a name with no
  database. The variable is the bare table name; `t_` stays only for a table named like a
  Python word (`ops.class` gives `ops__class.py` holding `t_class`), since the file name can no
  longer shadow a module.
- DESCRIBE's comments go into `Table`'s new `descriptions={column: text}` (left out when there
  are none); `Table` refuses a description of a column it doesn't have, or one that isn't text.
- Below `Table(...)`, a commented Aliases heading: the import line naming the folder the file
  was written into, a column Alias and a condition Alias example on a column that is neither an
  id nor the Date partition.
- How-tos 02 and 19 and the starter Templates `notebook_start` and `keep_table_references_true`
  follow the new names (new placeholders `<REFERENCE_FILE>`, `<KEPT_REFERENCE_FILE>`); ticket
  09 turns those Templates into how-to steps and ticket 10 rewrites how-to 02.
- The Example projects keep their table-named files: `tools/example_project.py` renames each
  written file and its Aliases import until ticket 09 lays them out as Projects.

## Reviews

- Spec (2026-10-21): nothing missing. Answered: the refusal of a name with no database is now in
  CHANGES.md; the Template edits and the Aliases prose in how-to 02 are needed now, since the
  file names changed under them, and are redone by 09 and 10.
- Standards (2026-10-21): the Aliases heading's import line was hard-coded to `references.`
  (now from `folder=`); a misnamed `date_partition` parameter (now the module the file is
  imported by); line widths (the heading is 92 wide, so the docstring's copy fits 96; the
  Templates and `create_table` rewrapped); a quoted `fix=`. Answered: `descriptions` is an
  argument, not a domain word, so CONTEXT.md is unchanged; `folder=` is the map's
  ("`write_table_reference` ... takes `folder=`").
- Beginner reader (2026-10-21): the same hard-coded import (fixed, and the Example projects'
  files now say `from table_references.job_runs import ...`); "description" meant two things in
  how-to 02 (the TODO is now "the line at the top that says what one row is"); "the output and
  the lineage" (now "the Hive, and the DataFrame run gives back"); an id column as the Alias
  example (now the first column that is neither an id nor the day); "before 6.0" in a Template;
  why calendar no longer gets t_ (CHANGES.md says). Left for 09: `table_references/` in the
  Templates and Example projects beside `references/` in the docstring.
