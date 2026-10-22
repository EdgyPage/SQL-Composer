# Databases and the text of a table

Type: task
Status: open
Blocked by: 04
Size: M

## Question

The user (2026-10-21): "I want to be able to import a table and then .column to return the text
of the column I'm interested in so I can insert it in to a select statement. I think it would be
wise to cite the column using explicit db.table.column names." Asked the best way to reach a
column of a table of a database, "so I don't have to memorize function patterns", they chose
`from references import ops` and then `ops.jobs.job_id`. They write in JupyterLab 4.

What exists (2026-10-21):
- `str(jobs.job_id)` and `f"{jobs.job_id}"` already give `jobs.job_id`, and `f"{c:>20}"`
  raises a TypeError.
- FROM writes `ops.jobs AS jobs`.
- `Table.__dir__` lists the columns, so the kernel completes them.
- Table references are flat files, `references/<db>__<table>.py`.
- Hive refuses three-part column names in a SELECT.

## Done when

- `references/__init__.py` holds one object per Database the Table references name, each
  attribute one of its Table references, imported from its own file. The objects are made by
  the Project actions, never by hand: `start`, `add_references`, `new_table`, `remove_table`,
  `remove_reference` and `refresh_reference_sheet` all keep the file current. The Registry knows
  it, and `project.check()` doesn't report it as made by hand.
- `from references import ops` gives the Database. `ops.jobs` is that Table reference's
  `Table`, and `ops.jobs.job_id` its Column. The kernel completes each step through `__dir__`.
  A wrong name gives the Toolbox's message, with the names there are and a close match, as a
  wrong column does.
- `str(ops.jobs)` and `f"{ops.jobs}"` give `ops.jobs AS jobs`; a Derived table gives its name.
  A column's text stays `jobs.job_id`. A format spec works on both as on a `str`. So
  `f"SELECT {ops.jobs.job_id} FROM {ops.jobs}"` is Hive that runs, and a Worked example shows
  it run through `unchecked_hive`.
- A Database whose name isn't a Python name, or that clashes with a word of Python, is
  refused when the file is written, saying how to import its references instead.
- The importing rules of the Levels still hold: `references/__init__.py` is Level 0, and the
  Level check reads it.
- CONTEXT.md, in the words grilled on 2026-10-21. A new entry, **Database**: "A named group of
  tables in the warehouse, the first part of a table's name (`ops` in `ops.jobs`). In a
  Project, each Database the Table references name is one Python object whose attributes are
  its tables, so a column is reached as `ops.jobs.job_id`." Its _Avoid_ is `schema, namespace`.
- CHANGES.md says how to start using it: run `refresh_reference_sheet` once.
- CLAUDE.md's Definition of done, the beginner reader included.
