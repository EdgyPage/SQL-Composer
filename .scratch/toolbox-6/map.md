# Toolbox 6.0: one Toolbox, and Projects

Label: wayfinder:map

The user (2026-10-20) asked for four things: stop maintaining Spark Composer and fold the Composer
core into sqlglot Composer; keep the README a tutorial that points into the how-tos, with the
version history apart; a Project layout made by an admin folder, with a notebook per Saved table,
lineage history kept beside it, and a flat folder of Table references feeding a Reference sheet;
and a prototype of that layout first, to give input on before it is built. A grilling session
settled the design below; this map is the design document, built out ticket by ticket.

## Notes

### Spark and the one Toolbox

- **Spark Composer is dropped.** Before anything is removed, tag `last-spark-composer` on the last
  dev commit that has both Editions (and note the last two-Edition export of main, `e60445c`).
  Then delete `spark_composer/`, `tests/spark_edition/`, Spark's CI job, its requirements
  section, the Java and Spark network-trap code, `--edition`, and every Spark branch in shared
  tests and tools. A new ADR supersedes ADR 0002.
- **One folder, `sqlglot_composer/`.** `composer_core/` merges into it; users' imports don't
  change. `tools/editions.py`, the name swap, and the parity tests go. CONTEXT.md drops Edition
  and Composer core, and Toolbox becomes one folder. A new ADR supersedes ADR 0003.
- **The version is 6.0, from the first commit** (ticket 03), since the merge already breaks old
  copies; CHANGES.md's `## 6.0` grows with each ticket. No export until the whole of 6.0 is done.

### The README and the history

- The Clean branch README (`docs/clean-branch-readme.md`) becomes a tutorial: install, start a
  Project, add references, add a Saved table, trace it, each step linking its how-to. "Update
  from 4.x", "Update from 3.x" and the sections that say what a version added move to
  `CHANGES.md`, which ships at main's top beside the README. Spark's sections go.
- A test holds it (no version headings or "Update from" sections; every how-to it names exists)
  and the drift reviewer's standing-docs kind gains a line saying so.

### Projects (the user's answers, 2026-10-20)

- **Layout.** A Project holds `sqlglot_composer/`, `admin/`, `references/` (flat, Level 0),
  `building_blocks/` (Level 1, .py), `tables/<db>__<table>/` (one Table folder per Saved table
  the user builds: `<db>__<table>.ipynb` and `lineage/`), `send.py` at the top (the user's
  `send`, written once; every notebook does `from send import send`; Level 0), and, if wanted,
  `settings.py` at the top (Level 0; `check()` and the Reference sheet ignore both).
- **Names are `<db>__<table>`** everywhere a file or folder is named for a table, since `-` and
  `.` can't be imported and `__` splits back unambiguously. Lineage files are
  `<YYYYMMDD-HHMMSS>-<db>__<table>.html/.md`.
- **Imports.** Each Table notebook's first cell puts the Project folder on `sys.path` in two
  plain lines (`pathlib.Path.cwd().parents[1]`; an admin notebook's is `.parent`), then imports
  what it calls and `from send import send`. References are imported as
  `from references.<db>__<table> import <table>`; a reference file's variable stays the bare
  table name.
- **The `project` module**, imported by name like `admin`: `start`, `new_table`,
  `remove_table`, `remove_reference`, `register`, `check`, `add_references`,
  `refresh_reference_sheet`, `load`, `run_tables`. `admin` stays warehouse-only. Inside a
  Project, Project actions and Admin statements both log to `admin/admin_log.md`, whichever
  notebook runs them.
- **`start()`** is run once from a notebook beside a freshly copied `sqlglot_composer/`. It makes
  `admin/` (its notebooks `new_table`, `remove_table`, `add_references`,
  `refresh_reference_sheet`, `check_project`, `run_tables`, `change_a_saved_table`;
  `templates/` copied from the Toolbox; `admin_log.md`; `registry.csv`), `references/`,
  `building_blocks/`, `tables/` and `send.py`, and refuses if any exists.
  The shipped Templates therefore live inside `sqlglot_composer/`.
- **`new_table("db.table", template="daily_table")`** refuses if the Table folder exists or
  the registry lists it. It makes the Table folder, its notebook from
  `admin/templates/<template>.py` (cells split on `# %%`, `# %% [markdown]` for a text cell;
  the placeholders `<DB>`, `<TABLE>` and `<NAME>`, the `<db>__<table>` form, filled in, every
  other `<...>` left for the user, as Templates' placeholders always are), an empty `lineage/`, and the Saved table's hand-fill Table reference in `references/`
  (kept if already there); it registers and logs. It never touches the warehouse.
- **The standard cells** (the shipped `daily_table` Template), after a text cell naming the
  table: 1 the Project path, the calls the other cells make, `send` and `DAY`; 2 the
  `# logic` cell, which only imports (the Toolbox names, references and Building blocks it
  reads) and defines `create()`, `rows(first, last)` (the clauses the steps share),
  `preview(day)`, `write_day(day)`, `backfill(first, last)`; 3 try it (`show_hive`,
  `run(preview(DAY))`); 4 `export_lineage(write_day(DAY))`; 5
  `project.refresh_reference_sheet("db.table")`. The logic cell holds its own imports because
  `load` runs it alone. Editing a Template changes only notebooks made after.
- **`load("db.table")`** reads that notebook's `# logic` cell and returns its functions; it
  refuses a logic cell that calls `run`. This is what lets lineage cross Table folders,
  `run_tables` order them, and tests run the Example projects.
- **`run_tables(day, send=..., tables=None)`** sends each chosen table's `write_day(day)`
  (all registered tables by default), writers before readers, as lineage already orders them;
  it refuses a loop. With no `send` it prints every Hive in order and sends nothing (a dry
  run).
- **Lineage.** `export_lineage` stays the one call. Given one Statement that writes a Saved
  table, inside a Project, its default name is the Table folder's
  `lineage/<YYYYMMDD-HHMMSS>-<db>__<table>.html/.md`; each run adds a pair, so the folder is
  the history. The commit stays in the footer. Outside a Project, naming is as in 5.x.
- **Removing** never deletes: `remove_table` moves the Table folder to
  `admin/removed/<YYYYMMDD-HHMMSS>-<db>__<table>/` and keeps the table's reference file, since
  the table is in the warehouse until `admin.drop_table`; `remove_reference` archives a
  reference file the same way; both log. Dropping the table in the warehouse stays `admin.drop_table`.
- **The registry**, `admin/registry.csv`: `kind, table, created_at, removed_at`, one row per
  Table folder and reference file a Project action made. `check()` reports, refusing nothing,
  any Table folder or reference file not registered (a rogue one) and any registered one
  missing on disk. `register(...)` adopts a hand-made one. It runs from
  `admin/check_project.ipynb` only; no other Project action runs it or waits on it.
- **`write_table_reference`** writes `<db>__<table>.py`, takes `folder=`, drops the `t_` rule,
  and fills `Table`'s new optional `descriptions={column: text}` from DESCRIBE's comments.
- **Aliases** are plain Python names below `Table(...)` in a reference file, under a commented
  heading with examples: a column by a plainer name (`minutes = job_runs.duration_mins`, a
  shorter name only; the Hive and output keep the real name) or a condition on that table
  alone (`failed = equals(job_runs.status, "FAILED")`).
- **`add_references(["db.table", ...], send=...)`** writes each one into `references/`; it
  skips, and logs, one already there and one whose DESCRIBE fails, finishes the list, then
  raises one error naming every skipped table and why.
- **The Reference sheet**, `references/reference_sheet.csv`: one row per column of every
  Table reference: `table, column, type, date_partition, in_key, aliases, description,
  exported_at`. Rebuilt from the reference files: `refresh_reference_sheet()` all of them,
  with a name only that table's rows. Column Aliases are listed beside their column;
  condition Aliases aren't in it.
- **Templates** become `admin/templates/`, the user's copy-and-paste section: the Table-notebook
  Templates (`daily_table`, `incremental_load`, `weekly_rollup`, `as_of_lookup`,
  `quality_checks`), the Saved-table reference Template `new_table` fills, and the Building
  block Template, copied by hand. `notebook_start` and `keep_table_references_true` become
  how-to steps.
- **Example projects** are rebuilt as real Projects (starter and intermediate), with
  `admin/`, `registry.csv` and lineage history; their generator pins the time, so regenerating
  adds no files.

### The docs

- How-to 01 becomes "Start a Project": the annotated layout, what each folder is for, the two
  path lines and why. 02 becomes "Add your tables' references" (bulk, Aliases, descriptions).
  New: "Add a Saved table", "Lineage across your tables", "The Reference sheet". The others keep
  their jobs in the Project's layout and import names. The README tutorial walks the same path.

## Tickets

- [01 Prototype a Project](issues/01-prototype-a-project.md)
- [02 Remove Spark Composer](issues/02-remove-spark-composer.md)
- [03 One folder, version 6.0](issues/03-one-folder-version-6-0.md)
- [04 README as a tutorial](issues/04-readme-as-a-tutorial.md)
- [05 Table references for Projects](issues/05-table-references-for-projects.md)
- [06 The project module](issues/06-the-project-module.md)
- [07 Load, run_tables and lineage history](issues/07-load-run-tables-and-lineage-history.md)
- [08 References in bulk and the Reference sheet](issues/08-references-in-bulk-and-the-reference-sheet.md)
- [09 Templates and Example projects as Projects](issues/09-templates-and-example-projects-as-projects.md)
- [10 How-tos and the README tutorial](issues/10-how-tos-and-the-readme-tutorial.md)

Tickets 02-04 don't wait for the user's review of 01; 05-10 do.

## Records this changes

- CONTEXT.md (2026-10-20): new words Project, Table folder, Project action, Reference sheet,
  Alias; Admin log widened to Project actions. Edition and Composer core leave with ticket 03.
- ADRs: Spark Composer dropped (supersedes 0002, ticket 02); one Toolbox folder (supersedes
  0003, ticket 03); a Table notebook's logic is loaded from its `# logic` cell, not imported
  from a .py (ticket 07).

## Decisions so far

- [01 Prototype a Project](issues/01-prototype-a-project.md): the user took the layout as
  built (2026-10-20), on branch `prototype/toolbox-6-project`; the Notes above now carry its
  three changes (five standard cells with imports in the logic cell, `<DB>`/`<TABLE>`/`<NAME>`
  placeholders, `send.py`) and the review's answers (removing keeps the reference, a dry run
  for `run_tables`, `check()` report-only, names and sheet columns as built).

## Not yet specified

- Nothing yet.

## Out of scope

- Running notebooks from a scheduler, and any notebook library (nbformat, jupytext, papermill):
  an .ipynb is written and read as plain JSON.
- Dialects other than Hive (ADR 0001).
