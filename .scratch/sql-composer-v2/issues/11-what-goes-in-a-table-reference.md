# What goes in a Table reference, and is it written or generated?

Type: grilling
Status: resolved
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

## Answer

**One `Table(...)` call per file, generated once from `DESCRIBE` and then owned by the user.**

```python
"""ops.job_runs - one row per job run."""
from sql_composer import Table, not_equals

job_runs = Table(
    "ops.job_runs",
    columns={
        "run_id": "bigint",           # unique run identifier
        "status": "string",           # SUCCESS / FAILED / TEST
        "avg_retry_secs": "double",
        "started_at": "timestamp",
        "dt": "string",
    },
    date_partition="dt",
    key=["run_id"],
    does_not_add_up=["avg_retry_secs"],
)


def real_runs():
    """Filter: leave out test runs."""
    return not_equals(job_runs.status, "TEST")


key_columns = [job_runs.run_id, job_runs.status, job_runs.started_at]
SITES = ["LON", "PAR", "NYC"]
```

**What a Table reference carries:**

- **Columns, one line each, with their Hive types** as Hive prints them (`"bigint"`,
  `"decimal(10,2)"`, `"array<string>"`). `None` means "don't know", and that column falls back to
  the plain rules from the guardrails ticket. The type-checking Guards skip complex types.
- **`date_partition` is required.** A table with no Date partition says `date_partition=None`
  out loud, so forgetting it can't silently switch off the both-ends date bound.
- **`key` is optional** and defaults to none. With no key, a `JOIN` onto the table refuses unless
  it carries `many_matches=True`.
- **`does_not_add_up`** lists the columns that the unsafe re-grouping Guard treats like a distinct
  count or an average.
- **`date_format`** appears only when the partition's dates aren't `'YYYY-MM-DD'`, for example
  `date_format="%Y%m%d"`. The time zone isn't an argument, and the docstring notes it.
- **No `alias`.** In the SQL the table is called by its short name (`job_runs`).
- **The one-line description is the file's docstring.**
- **`Table(...)` checks itself when it's imported.** It refuses, naming the offender, if
  `date_partition`, `key` or a `does_not_add_up` entry isn't one of its columns, or if
  `date_format` isn't a valid pattern.

**Below the call:** filters that concern that table alone, as plain functions (anything involving
two tables is a Building block), and plain Python lists the user keeps by hand, such as columns of
interest or site codes. `SELECT` and `any_of` accept a list as well as separate arguments. There
are no per-file standard queries. The "first look" is a Toolbox function, `first_look(t)`, that
works on any Table reference: all columns, the last day, 20 rows. "Latest partition" means "the
last N days", because `MAX(dt)` may scan the whole table.

**Generated once, then yours:** `write_table_reference("ops.job_runs", send=run_query)`

- sends `DESCRIBE` and `SHOW PARTITIONS` through the user's own `send`. Both read metadata, not
  rows, and the user confirmed both are fine to send at work. `DESCRIBE` returns a DataFrame of
  `col_name`, `data_type`, `comment`, including the partition rows;
- writes `job_runs.py` next to the notebook, with a variable named after the short table name,
  Hive's column comments as line comments, and TODOs for the docstring, `key` and
  `does_not_add_up`;
- **refuses if the file exists** and writes nothing. It is never regenerated, so there are no
  generated sections and no second file to import;
- **picks the Date partition as follows.** No partition columns: `None`. Otherwise it takes the
  first (outermost) partition column, with a `# TODO check: also partitioned by ...` comment when
  there are several. If that column's newest value doesn't parse as a date, it writes `None` with
  a TODO naming the partition columns. The newest value also sets `date_format` when needed;
- **never guesses a key.** Counting rows against distinct values is a real query against a
  multi-million-row table, and a column unique for one day can repeat across days.

The user's proposed name `RECORD(table)` was dropped, because upper case is kept for clause
functions.

**A Saved table's Table reference is written by hand**, in the same shape with every column typed.
Generating it from the Statement that writes it is circular (`INSERT_OVERWRITE(t)` needs `t` to
exist) and would have to guess the types of calculations. The line-up Guard and `create_table`'s
refusal of untyped columns cover the risks.

Handed on:

- **"What's in the Toolbox?"** It gets `Table`, `write_table_reference`, `first_look`, list
  arguments for `SELECT` and `any_of`, a candidate `check_key(t, send=...)` that confirms a
  declared key over one bounded day, and a way to name a table twice in one Statement (self-joins,
  and two tables with the same short name such as `ops.jobs` and `mart.jobs`).
- **The schema-drift fog** is sharp enough to ticket: see "Does the Toolbox check a Table reference
  against the warehouse?".

**Changed by "What does the Example database demonstrate, and where does it run?" (2026-09-25).**
A `JOIN` onto a table with no key now warns instead of refusing. The warning says to declare
`key=[...]`, and `many_matches=True` still silences it.
