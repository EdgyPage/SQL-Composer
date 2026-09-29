# The 3.0 Hive changes both Editions share

Type: task
Status: open
Blocked by: 04, 21, 23, 24

## Question

The user approved these changes to SQL Composer's own Hive (2026-09-29), so both Editions write
the same text. Each changes the shared tree or a shared list, so both printers follow. One commit
each, with ticket 4's evidence cited:

- **`CAST(... AS STRING)` around week_start and month_start.** Spark's NEXT_DAY and TRUNC return
  DATE while the Toolbox types both results as string; Hive's results don't change.
- **Backticks for Spark's reserved words** (such as ANTI, SEMI, MINUS, EXCEPT, NATURAL, SETMINUS,
  as ticket 4 lists them), in column and table names, DESCRIBE and SHOW PARTITIONS included.
- **Strict create_table types:** only types on an explicit Hive list, in `trees.py`, instead of
  whatever sqlglot's `DataType.build` accepts.
- **The shared hive_function argument and aggregate list in SQL Composer too**, so the same
  Guards fire in both Editions. SQL Composer's answer changes for names such as lag, first and
  count_if.

Each commit regenerates both goldens and both galleries, updates the doctests, and removes the
strict xfails that waited for it. The drift reviewer opens a `version` item for each; answer it
"folds into 3.0" and leave it open until ticket 26. Open items freeze exports, so run tickets 25
and 26 back to back.

## Done when

The Definition of done in `CLAUDE.md` holds, except the open version items this ticket lists for
26; both runs and all four CI jobs are green with no strict xfail left; the parity test passes
with only the division and hive_function rows.
