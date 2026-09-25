# What goes in a Table reference, and is it written or generated?

Type: grilling
Status: claimed
Blocked by: 01, 02

## Question

A Table reference is the Level 0 script for one table. It exposes the table's columns as
attributes, so a typo fails at import, together with the table's standard queries. Decide:

- what else it carries - column types, partition columns, a key, a one-line description;
- what a "standard query" is - for example the usual filters already applied, or the latest
  partition;
- whether the file is written by hand, or generated from a `DESCRIBE` run through the API and then
  edited. That depends on what the API returns.

## Comments

**From "Which guardrails on how a Statement is written earn their place?" (2026-09-25).** The Guards need three things from a Table reference:

- **a declared key.** `JOIN` onto a table with no key refuses unless it's given
  `many_matches=True`;
- **optional column types.** A typed column gets its values checked (`equals(runs.dt, 20260925)`
  against a string column refuses) and dates formatted to fit it. An untyped column falls back to
  the plain rules: a date becomes `'YYYY-MM-DD'`, and a timestamp with a time of day refuses;
- **a way to mark a column as not safe to add up,** for pre-summarised warehouse tables (distinct
  counts, averages, ratios).

**The user's idea (2026-09-25), raised during the guardrails grilling.** A function the user calls
once on an unknown table, which writes the Table reference file for them, above all its columns. The
user then adds the attributes that only they know by hand, such as "columns of interest" and "site
locations". The user doubts that those can be inferred from column names. Points to settle here:

- **What a metadata query can fill in:** column names, types, comments and partition columns
  (`DESCRIBE FORMATTED` or `SHOW CREATE TABLE`). It can't fill in the key (Hive doesn't enforce
  one), the columns that aren't safe to add up, or anything about meaning. Guessing a key by
  counting rows is a real query against a multi-million-row table, which load safety has to allow.
- **Regenerating mustn't overwrite the hand-written part.** Options: a generated file plus a
  hand-written file that imports it, or one file with a generated section that's rewritten in
  place.
- **Name:** the user proposed `RECORD(table)`. Upper-case names are reserved for clause functions,
  so this one wants a lower-case name.
- **It depends on what the query API returns** for a `DESCRIBE`, which the user knows from daily
  use. It reads metadata, not rows, which fits the "no probing at work" rule, but the user should
  confirm.

**From "How much may a Statement touch and return by default?" (2026-09-25).** A Table reference names
its **date partition column**. Every Statement that reads the table must bound that column at both
ends unless the read carries `reads_all_partitions=True`, and `by_day` splits on it. Other
partition levels stay optional. The user's tables are partitioned by one date column, UTC or local.
Suggested: a "first look" standard query, meaning all columns of the latest day capped at a few
rows (`all_columns(t)`, `last_n_days(t.dt, 1)`, `LIMIT(20)`), since the Toolbox has no preview
function. A key-guessing row count is an ordinary bounded Statement, which the load defaults allow.

**From "How do pieces combine across Levels - CTE, subquery, or saved table?" (2026-09-25).** A Saved table
(one a Statement writes on the server, then read back like any table) is described by an ordinary
Table reference, with two extra demands. Every column must have a type, because
`create_table(t)` generates `CREATE TABLE IF NOT EXISTS ... PARTITIONED BY (dt STRING) STORED AS
ORC` from it and refuses untyped columns. Its column order is the order the table is written in,
because `INSERT_OVERWRITE(t)` lines the `SELECT` up by name into that order. Decide here whether a
Saved table's Table reference is written by hand or generated from the Statement that writes it.
