# Load, run_tables and lineage history

Type: task
Status: resolved
Blocked by: 06
Size: M

## Question

Map Notes, "load", "run_tables", "Lineage". `project.load("db.table")` returns the `# logic`
cell's functions and refuses one that calls `run`; `run_tables(day, send=..., tables=None)`
orders writers before readers and refuses a loop; `export_lineage`'s default name inside a
Project. Write the ADR on loading the logic cell rather than importing a .py.

## Done when

- Lineage across two Table folders, through `load`, is tested.
- The pytest runs pass, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).

## Answer

Built 2026-10-21 on branch `toolbox-6/07-load-run-tables-lineage`.

- `project.load(name)` reads `tables/<db>__<table>/<db>__<table>.ipynb` as JSON, takes the code
  cell whose first line is `# logic`, refuses one that isn't Python yet (a `<...>` left in) or
  that calls `run`, puts the Project on `sys.path`, drops the `references` and
  `building_blocks` modules Python holds so it reads them as they are now, and runs the cell
  with `exec`, returning a `TableLogic` of the functions it defines. The `exec` is the one
  reviewed ALLOWED site for it, with the user's OK (2026-10-21).
- `project.run_tables(day, send=None, tables=None)`: every Table folder the registry lists, or
  `tables`; each one's `write_day(day)` through `load`, in lineage's order (`in_order`, which
  refuses a loop). With no `send` it prints each Hive under `-- n of m: name`; with one, it runs
  each, reports "n of m: name  worked", and stops at the first that fails.
- `export_lineage` of one Statement that writes a Saved table whose Table folder is in the
  Project (found from the calling file's folder, or else the folder Python is working in)
  goes to `tables/<db>__<table>/lineage/<YYYYMMDD-HHMMSS>-<db>__<table>.html/.md`; anything
  else is named as in 5.x. `to=` still wins.
- `start()` writes `admin/run_tables.ipynb`. ADR 0010 records loading the logic cell.

## Reviews
