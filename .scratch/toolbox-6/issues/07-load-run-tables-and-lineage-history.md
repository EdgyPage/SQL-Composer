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

- Spec (2026-10-21): the module docstring said only add_references touches the warehouse and
  every action logs (now it names the Project actions that log, and says run_tables writes
  through your send); `# logical ...` passed for the logic cell (now the first line must be
  `# logic` exactly); `run` imported under another name slipped through (now caught).
  Answered: load gives the functions only, and says so; run_tables stops at the first failure,
  takes a bare name in `tables`, and returns a report, recorded in the map; the Table folder
  must exist for its lineage naming, recorded too.
- Standards (2026-10-21): widths fixed; "history" is the Admin log's avoid-word, so lineage
  says "past Lineage"; the stem rule is `project.table_stem`, which lineage shares; load's
  reading and refusing is `_checked_logic`. Left: `TableLogic` stays a small class, for its
  repr naming the functions it holds.
- Beginner reader (2026-10-21): a loop refused by run_tables named export_lineage and its fix
  (now `in_order` takes the call, and run_tables' refusal says to change one table's logic or
  leave it out); load's fix pointed at check_project, which doesn't list Table folders (now
  "the Table folders are in tables/"); the line number in "isn't Python yet" was one short; a
  failed run hid the tables already written (now each prints as it works); "writers first"
  (now "each before the tables that read it"); "one Statement" in export_lineage (now
  "exactly one"); the run_tables notebook's text and CHANGES.md's long sentence reworded.
