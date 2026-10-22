"""Add your tables' references

For: Getting started

## Goal

Get every column of the tables you read, each name and its Hive type, into your Project without
typing them. `project.add_references` asks each table itself and writes its Table reference, a
small .py file describing the table, into the Project's `references/` folder. You fill in what
it can't know, add Aliases, your own names for its columns and conditions, check the file
against the table, and then build Statements from its columns: all of them at once, or the ones
a list of names picks.

## When you'd use it

The first time you read a table at work, and whenever your notebooks start reading another. A
Statement reads a table through its Table reference, so every table you read needs one, and a
table with forty columns is forty chances to mistype a name or a type. Write them instead, many
at once, and every notebook of the Project imports them from `references/`.

A table that doesn't exist yet, such as a Saved table (a table of your own, which your
Statements write into) you are about to create, has nothing to ask: describe it by hand, as
[Describe a table by hand](#describe_a_table_by_hand) shows, or let
[Add a Saved table](#add_a_saved_table) write its file for you to fill in.

## Steps

### Start a Project

These steps run in a Project, as [Start a Project](#start_a_project) makes one. In your own Project, which is started already, leave out `project.start()`: it refuses a
folder that is a Project. This page has none, so it starts one:

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/ and warehouse.py. Next: write your query and execute in warehouse.py.

Every step here passes `query=example_database.query`, the Example database's own query. At
work, pass your own, `from warehouse import query`, and name your own tables.

### See what the table says about itself

A table in the warehouse can describe itself. The Hive command DESCRIBE lists its columns and
their types, and SHOW PARTITIONS lists the Partitions it holds. Neither reads a single row, so both
are quick on the biggest table. Here is what DESCRIBE says of `ops.run_alerts`, sent straight
through the Example database's query:

>>> example_database.query("DESCRIBE ops.run_alerts")
                  col_name  data_type     comment
0                 alert_id     bigint
1                   run_id     bigint
2                 severity     string  low / high
3                       dt     string
4                                 NaN         NaN
5  # Partition Information        NaN         NaN
6               # col_name  data_type     comment
7                       dt     string

The first four rows are its columns. The fifth is a blank line DESCRIBE leaves before its next
section: its name is empty, and its other two cells are missing, NULL in Hive, which the table
on the how-to page shows as NULL and pandas 3 prints as NaN. The rows under
`# Partition Information` say which columns split the table into Partitions: here dt alone,
one Partition a day.

### Write your tables' Table references

`project.add_references` takes a list of tables. For each, it sends those two commands through
your query, turns what comes back into a Table reference file in `references/`, and adds it to
the registry, admin/registry.csv; then it logs what it did in the Admin log:

>>> project.add_references(["ops.jobs", "ops.job_runs", "ops.run_alerts"],
...                        query=example_database.query)
Wrote references/ops__jobs.py, references/ops__job_runs.py and references/ops__run_alerts.py: fill in their TODO lines.
Wrote references/ops.py: from references import ops gives ops.job_runs, ops.jobs and ops.run_alerts.
Restart the kernel of a notebook that imported references, to see a table added since.

Each file is named after the database and the table joined by two underscores, `ops.jobs`
giving ops__jobs.py, since a dot or a dash can't be in a name Python imports. The variable in
it is named after the table alone, jobs. A table named like a word Python keeps for itself,
such as class, gets t_ in front of its variable: `ops.class` would give ops__class.py, holding
t_class.

The second line is the file for the Database ops, the first part of each table's name:
references/ops.py, which the Project actions write again each time a Table reference is added
or archived, and you never edit. In a notebook of the Project, `from references import ops`
gives each table by its name, `ops.jobs`, and each column as `ops.jobs.job_id`, so tab
completion lists them at each dot. A file still to fill in joins it once it is filled in and
`project.refresh_reference_sheet()` runs.

Open references/ops__job_runs.py, which the page shows above. It imports `Table`, then makes
one variable,
`job_runs`:

- `columns` holds every column and its type;
- `partitioned_by=["dt"]` comes from DESCRIBE's `# Partition Information` rows;
- three lines say TODO: the line at the top that says what one row is, `key=None` and
  `does_not_add_up=[]`. The table can't tell anyone those, so the file leaves them to you;
- `descriptions=` holds what each column holds, in words, from its comment in the warehouse,
  such as status's `SUCCESS / FAILED / TEST, NULL while running`;
- under the Aliases heading at the end, commented-out examples show how to add your own names
  for the table's columns and conditions, as Fill in the TODOs, below, does.

### Fill in the TODOs

Open references/ops__job_runs.py in your editor and replace the three TODO lines. This is the
file with them filled in, and two Aliases of your own under its Aliases heading, whose comment
lines are left out here:

    \"\"\"ops.job_runs - one row per run of a job.\"\"\"
    from sqlglot_composer import Table, equals

    job_runs = Table(
        "ops.job_runs",
        columns={
            "run_id": "bigint",
            "job_id": "bigint",
            "status": "string",
            "duration_mins": "int",
            "avg_retry_secs": "double",
            "dt": "string",
        },
        partitioned_by=["dt"],
        key=["run_id"],
        does_not_add_up=["avg_retry_secs"],
        descriptions={
            "status": "SUCCESS / FAILED / TEST, NULL while running",
        },
    )

    # --- Aliases ---------------------------------------------------------------------------
    minutes = job_runs.duration_mins
    failed = equals(job_runs.status, "FAILED")

- The first line says, in your own words, what one row is.
- `key=` lists the columns that pick out one row. Every run has its own `job_runs.run_id`, so
  it is `key=["run_id"]`. Ask whoever owns the table if you aren't sure: `check_key`, below,
  checks it. JOIN uses the key to warn you when a join would repeat rows.
- `does_not_add_up=` lists the columns that are averages, ratios or counts of different values.
  `job_runs.avg_retry_secs` is each run's average wait between retries: adding up two runs'
  averages gives a number that means nothing, so the Toolbox refuses to add it up once it is
  listed here.
- An Alias is your own name, written by hand. `minutes` is a shorter name for
  `job_runs.duration_mins`, for you: the Hive, and the DataFrame `run` gives back, still call
  the column duration_mins. `failed` names a condition on this table alone, for `WHERE` or
  `count_rows(where=...)`. Add `equals` to the import at the top, beside `Table`, since
  `failed` calls it.
- `descriptions=` is yours too: add what a column holds where the warehouse has no comment, as
  `"duration_mins": "how long the run took, in minutes"`.

Then import the file in any notebook of the Project by its folder, references, with the
Aliases you use beside the table:

    from references.ops__job_runs import job_runs, minutes, failed

Run `project.refresh_reference_sheet()` after you fill a file in: the Reference sheet lists
every column of every Table reference, with its Aliases and description, as
[The Reference sheet](#the_reference_sheet) shows.

The Example database ships this same Table reference, filled in the same way, so the steps
here use its copy:

>>> job_runs = example_database.job_runs

### Check the file against the table

`check_table_reference` asks the table for its columns again and compares them with the file.
Run it after you edit a Table reference, and whenever the table may have changed:

>>> check_table_reference(job_runs, query=example_database.query)
ops.job_runs matches its Table reference.

When something differs, it lists each problem with the line to change in the file. It never
edits the file itself. A table that changed, and what it says then, is in
[Keep a Table reference true over time](#keep_a_table_reference_true_over_time).

### Check the key you wrote

The warehouse never checks a key: nothing stops two rows sharing one `job_runs.run_id`.
`check_key` counts the rows for each key on the rows `where=` picks, and lists any key that
repeats. `job_runs` is partitioned, so say which Partitions to check, here one day's:

>>> check_key(job_runs, query=example_database.query,
...           where=equals(job_runs.dt, "2026-09-24"))
ops.job_runs: the key (run_id) holds where job_runs.dt = '2026-09-24'.

`reads_all_partitions=True` in place of `where=` checks the whole table. A table that isn't
partitioned is always checked whole.

### Take a first look at the rows

`first_look` builds an ordinary Statement that reads every column and the first 20 rows the
warehouse comes to, so it is quick to run on a big table: `LIMIT 20` stops the read early.
`show_hive` prints its Hive, and `run` runs it:

>>> text = show_hive(first_look(job_runs))
SELECT
  job_runs.run_id,
  job_runs.job_id,
  job_runs.status,
  job_runs.duration_mins,
  job_runs.avg_retry_secs,
  job_runs.dt
FROM ops.job_runs AS job_runs
LIMIT 20;
>>> run(first_look(job_runs), query=example_database.query)
   run_id  job_id   status  duration_mins  avg_retry_secs          dt
0      95       1  SUCCESS             12             2.0  2026-09-23
1      96       2  SUCCESS             18             0.0  2026-09-23
2      97       3   FAILED             30             8.0  2026-09-23
3      98       2      NaN             15             NaN  2026-09-23
4      99       1     TEST              5             0.0  2026-09-23
5     101       1  SUCCESS             10             1.0  2026-09-24
6     102       2   FAILED             20             6.0  2026-09-24
7     103       3  SUCCESS             30             0.0  2026-09-24
8     104       1  SUCCESS             40             3.0  2026-09-24

The Example database's `job_runs` holds only nine rows, so all of them come back. Which 20 rows
a big table gives is up to the warehouse.

### Build a SELECT from every column

`all_columns` gives a Table reference's columns as a Python list, in the table's order:

>>> all_columns(job_runs)
[job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins, job_runs.avg_retry_secs, job_runs.dt]

`SELECT` takes a list as well as single columns, so `SELECT(all_columns(job_runs))` asks for
every column by name. Hive's `SELECT *` would ask for whatever the table holds on the day it
runs, so a column added later would quietly change your result; a list of names doesn't.

>>> every_column = statement(
...     SELECT(all_columns(job_runs)),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-23")),
... )
>>> text = show_hive(every_column)
SELECT
  job_runs.run_id,
  job_runs.job_id,
  job_runs.status,
  job_runs.duration_mins,
  job_runs.avg_retry_secs,
  job_runs.dt
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt = '2026-09-23';
>>> run(every_column, query=example_database.query)
   run_id  job_id   status  duration_mins  avg_retry_secs          dt
0      95       1  SUCCESS             12             2.0  2026-09-23
1      96       2  SUCCESS             18             0.0  2026-09-23
2      97       3   FAILED             30             8.0  2026-09-23
3      98       2      NaN             15             NaN  2026-09-23
4      99       1     TEST              5             0.0  2026-09-23

Run 98 is still running, so its status and its avg_retry_secs are missing: NULL. pandas shows
a missing value as NaN, a missing number and missing text alike (pandas 2 showed missing text
as None).

### Build a SELECT from a list of column names

Each column of a Table reference is one of its attributes, such as `job_runs.status`. When the
names you want come as text, from a list in your settings or from another table's columns, the
built-in Python function `getattr` takes the attribute by its name, so the list of names
becomes a list of columns:

>>> wanted = ["run_id", "status", "duration_mins"]
>>> columns = [getattr(job_runs, name) for name in wanted]
>>> columns
[job_runs.run_id, job_runs.status, job_runs.duration_mins]
>>> chosen = statement(
...     SELECT(columns),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-23")),
... )
>>> text = show_hive(chosen)
SELECT
  job_runs.run_id,
  job_runs.status,
  job_runs.duration_mins
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt = '2026-09-23';

A name that isn't one of the table's columns stops the list at once: see Common mistakes.

## Check it worked

The three Table reference files are in references/, and the registry lists each one:

>>> from pathlib import Path
>>> sorted(path.name for path in Path("references").glob("ops__*.py"))
['ops__job_runs.py', 'ops__jobs.py', 'ops__run_alerts.py']
>>> project.check()
Every Table folder and Table reference is registered, and each one registered is there.

Once you've filled in a file's TODOs, both checks pass for its table:

>>> check_table_reference(job_runs, query=example_database.query)
ops.job_runs matches its Table reference.
>>> check_key(job_runs, query=example_database.query,
...           where=equals(job_runs.dt, "2026-09-24"))
ops.job_runs: the key (run_id) holds where job_runs.dt = '2026-09-24'.

## Common mistakes

### A column name the table doesn't have

A Table reference is there so you never type a column's name as text. A misspelt column stops
the line it is on, and lists the columns the table has:

>>> job_runs.stauts
Traceback (most recent call last):
...
AttributeError: job_runs has no column 'stauts'. Did you mean 'status'? Its columns are: run_id, job_id, status, duration_mins, avg_retry_secs, dt.

A name in a list you pass to `getattr` is checked the same way:

>>> columns = [getattr(job_runs, name) for name in ["run_id", "duration"]]
Traceback (most recent call last):
...
AttributeError: job_runs has no column 'duration'. Did you mean 'duration_mins'? Its columns are: run_id, job_id, status, duration_mins, avg_retry_secs, dt.

Copy the name from the list the message gives, here `"duration_mins"`.

### Adding up a column that doesn't add up

With `job_runs.avg_retry_secs` listed in `does_not_add_up=`, a total of it stops as you build
it, before anything runs:

>>> total_wait = statement(
...     SELECT(AS(sum_of(job_runs.avg_retry_secs), "wait")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  sum_of(job_runs.avg_retry_secs) adds up job_runs.avg_retry_secs, which is listed in does_not_add_up in its Table reference.
...

`GuardRefused` is how a Guard stops: a check the Toolbox runs as you build a Statement, which
refuses one that would quietly give a wrong number. If you leave `does_not_add_up=[]` empty,
nothing stops it, and the total means nothing.

### Adding a table whose Table reference is already there

`project.add_references` never writes over a file: once written, the file is yours, and
writing it again would lose the key and the notes you added. A list that names a table
already in `references/` writes the others, skips that one, and then stops, naming it:

>>> project.add_references(["ops.jobs", "ops.scheduler_runs"], query=example_database.query)
Traceback (most recent call last):
...
sqlglot_composer.project.SkippedTables:
  What happened:  add_references skipped 1 of 2 tables: ops.jobs (references/ops__jobs.py is there already).
...

references/ops__scheduler_runs.py was written all the same, and the Admin log names the table
skipped. A table whose file is there needs nothing: edit the file instead, and run
`check_table_reference` to see what has changed in the table since.

### A key that doesn't pick out one row

The table ops.run_alerts has a run_id column too, and a run can raise several alerts. A key
of `["run_id"]`
looks right, but `check_key` shows the run_ids that repeat:

>>> wrong_key = Table(
...     "ops.run_alerts",
...     columns={"alert_id": "bigint", "run_id": "bigint", "severity": "string",
...              "dt": "string"},
...     partitioned_by=["dt"],
...     key=["run_id"],
... )
>>> check_key(wrong_key, query=example_database.query,
...           where=equals(wrong_key.dt, "2026-09-24"))
ops.run_alerts: the key (run_id) repeats where run_alerts.dt = '2026-09-24'. Keys with more than one row:
 run_id  copies
    101       3
    103       2

Its key is `["alert_id"]`: one row per alert.

## Next

- Describe a Saved table that doesn't exist yet, by hand:
  [Describe a table by hand](#describe_a_table_by_hand).
- Build your first Statement on the table and paste its Hive into another program:
  [Build a first Statement and paste its Hive](#build_a_first_statement).
- Read every column of the Project's tables in one place:
  [The Reference sheet](#the_reference_sheet).
- When a table gains or changes a column after you wrote its file:
  [Keep a Table reference true over time](#keep_a_table_reference_true_over_time).
- A table whose days are written like 20260924, and which is partitioned by a second column too:
  [A day written another way, and a second partition](#a_day_written_another_way).
- Each function here has a Worked example in the gallery:
  [`write_table_reference`](examples.html#write_table_reference), which writes one table's
  file, [`check_table_reference`](examples.html#check_table_reference),
  [`check_key`](examples.html#check_key), [`first_look`](examples.html#first_look) and
  [`all_columns`](examples.html#all_columns).
"""
