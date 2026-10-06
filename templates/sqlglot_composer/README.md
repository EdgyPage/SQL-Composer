<!-- sqlglot Composer 4.1, exported 2026-10-06 15:49 - copy it, then edit your copy -->
# Templates

Each file here is the empty shape of one of your own scripts. Copy it into your project, then
replace each placeholder, a word in angle brackets such as `<TABLE>`, brackets and all, with
your own. Each file's docstring says where to copy it, lists its placeholders under "Fill in:"
with an example for each, and names the Example project file it mirrors, filled in for the
Example database. Python stops at a placeholder left in, so a file can't run half filled in.

Your project's folder holds the Toolbox's two folders, `composer_core` and `sqlglot_composer`,
copied whole from the Toolbox you downloaded, and your own `table_references/`,
`building_blocks/` and `statements/`. These three are the Levels, 0, 1 and 2: a script imports
only from a lower Level and from the Toolbox, and a script beside them, such as
`run_pipeline.py`, sits above the Levels, so it may import from any of them.

To practise first, on the Example database's made-up tables, copy the `table_references/`
folders of `example_projects/sqlglot_composer/starter/` and `example_projects/sqlglot_composer/intermediate/` into your project:
their Table references are filled in. Then fill a Template in with the examples its "Fill in:"
block gives.

## The starter Templates, in order

| Template | What it is | What it needs first |
|---|---|---|
| `starter/notebook_start.py` | A notebook's first cells: your send, a first Table reference, a first Statement. | Nothing. |
| `starter/keep_table_references_true.py` | Writes the Table references of new tables, and compares those you keep with their tables. | Your send, from `notebook_start.py`. |
| `starter/building_block.py` | A Building block: one row per group and day. | The Table reference it reads. |
| `starter/saved_table_reference.py` | A Saved table's Table reference, by hand. | The Building block, whose names it repeats. |
| `starter/saved_table.py` | A Saved table's steps: create, preview, write a day, backfill. | The Building block and the Saved table's Table reference. |
| `starter/daily_pipeline.py` | Every step for one day, in order. | `saved_table.py`'s copy. |
| `starter/per_group_statement.py` | A Statement counting per group, keeping the groups that pass a test. | The Table reference it reads. |

`starter/saved_table.py` and `intermediate/incremental_load.py` are alternatives: use one of
them for each Saved table, not both. `saved_table.py` writes one day each run, and
`daily_pipeline.py` runs it; `incremental_load.py` writes the last few days again each run, and
`incremental_pipeline.py` runs it. A project with Saved tables of both kinds uses
`incremental_pipeline.py`, with each `saved_table.py` copy's `write_day(day)` in `steps(day)`:
`in_order` passes a single write through as it is.

## The intermediate Templates

| Template | What it is | What it needs first |
|---|---|---|
| `intermediate/incremental_load.py` | A Saved table whose every run writes the last few days again. | Copies of `building_block.py` and `saved_table_reference.py`. |
| `intermediate/incremental_pipeline.py` | Every step of a run, in order, for incremental loads. | `incremental_load.py`'s copy. |
| `intermediate/weekly_rollup.py` | Weekly totals, added up from a Saved table's days. | The Saved table's Table reference. |
| `intermediate/as_of_lookup.py` | Rows counted by what a snapshot table said on their own day. | The Table references of the rows and of the snapshot table. |
| `intermediate/building_blocks.py` | Building blocks built from other Building blocks: the keys missing on a day. | The Table references of the two tables. |
| `intermediate/quality_statements.py` | Repeated keys, NULL counts and rows per day, for one table. | Its Table reference. |
| `intermediate/settings_driven.py` | The same Statements for many tables, made from settings. | The tables' Table references. |

The starter Templates give `between(...)` its days as text, such as `"2026-09-24"`, written as
the table writes its days. `quality_statements.py` and `settings_driven.py` give them as a
`datetime.date`, which the Toolbox writes each table's own way, so one Statement serves tables
that write their days differently.

## Running them

Each step is sent through your send, the function `notebook_start.py`'s cell 1 writes, from a
notebook started in your project's folder. Import a Statement file by its Level folder, such as
`from statements import job_day_minutes`, then send a step with
`run(job_day_minutes.preview("2026-09-24"), send=send)`, or every step at once with
`send_all(send, day)` from your copy of a pipeline Template. How-to 1, Start a notebook, on
`how_to.html` in the `sqlglot_composer` folder, shows how to write your send.

Python reads a file once, when it is first imported. After editing one, restart the notebook's
Python before using it, or anything that imports it, again: `importlib.reload(...)` reloads only
the file you name, and a file that imported it keeps the old one.
