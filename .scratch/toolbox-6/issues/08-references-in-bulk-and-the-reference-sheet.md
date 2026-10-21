# References in bulk and the Reference sheet

Type: task
Status: resolved
Blocked by: 06
Size: M

## Question

Map Notes, "add_references", "The Reference sheet". `add_references` (skip, log, finish, one
error at the end) and `refresh_reference_sheet(name=None)` reading `references/*.py`, column
Aliases and `descriptions=`.

## Done when

- A run over a list holding existing and missing tables is tested, and refreshing one table
  replaces only that table's rows.
- The pytest runs pass, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).

## Answer

Built 2026-10-21 on branch `toolbox-6/08-references-and-sheet`.

- `project.add_references(names, send)` writes each table with `write_table_reference(...,
  folder=references/)` and registers it. A file already there, a name that isn't a table's
  with its database, and a table whose DESCRIBE fails (any error from the send) are skipped;
  the list is finished; one Admin log entry names the files written and each table skipped
  ("- Skipped:"), with "Result: failed, with SkippedTables"; then `project.SkippedTables`
  (a four-part message) names each skipped table and why, and what was written.
- `project.refresh_reference_sheet(name=None)` reads every `references/*.py` without running
  it, with `ast`: the first top-level `x = Table(...)`'s name, columns, Date partition, Key and
  `descriptions=`, and each top-level `alias = x.column` below it as a column Alias. The sheet
  is `table, column, type, date_partition, in_key, aliases, description, exported_at`, "yes"
  for the Date partition and Key columns, Aliases joined by "; ", sorted by table. With a name,
  only that table's rows are replaced. A file that doesn't parse yet (a `<...>` left in) is
  left out and named in the report. It isn't logged: like `check()`, it changes no file of the
  user's, only the sheet it rebuilds.
- The admin notebooks `add_references` and `refresh_reference_sheet` are written by `start()`.

## Reviews
