"""Add your tables' references

For: Getting started

## Goal

Get every column of the tables you read, each name and its Hive type, into your Project without
typing them. `project.add_references` asks each table itself and writes its Table reference, a
small .py file describing the table, into the Project's `references/` folder, with its Key
proposed and checked. You accept or change what it proposed, add Aliases, your own names for
its columns and conditions, and check the file against the table. Then
`from references import ops` gives each table of the Database `ops`, the group of tables whose
names start with `ops.`, by its name, and each column at a dot after it.

## When you'd use it

- If you read a table at work for the first time, or your notebooks start reading another,
  write its Table reference as the steps below do. A Statement, a query the Toolbox builds,
  reads a table through its Table reference, so every table you read needs one, and a table
  with forty columns is forty chances to mistype a name or a type. Write them many at once, and
  every notebook of the Project imports them from `references/`.
- If the table doesn't exist yet, such as a Saved table (a table of your own, which your
  Statements write into) you are about to create, there is nothing to ask:
  [Save a table](#save_a_table) writes its file for you to fill in, and
  [Describe a table by hand](#describe_a_table_by_hand) shows the file written in full.

## Steps

### 1. Set up the Project the last how-to left

Goal: a Project whose `references/` folder the steps below fill.
[Start a Project](#start_a_project) left a Project with nothing in `references/` yet. This page
has none, so it starts one; in your own Project, which is started already, leave
`project.start()` out. The star import brings every Toolbox name, such as `check_key` and
`equals`; the `project` module is imported by its name, since the star leaves it out:

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/ and warehouse.py.
Next: set conn, your connection, in warehouse.py.
>>> from warehouse import query, execute

Every step here passes that `query`; `execute` waits for a step that changes a table. Here it
runs on the Example database, the made-up tables that ship inside the Toolbox, as warehouse.py
holds it; at work it is your own, and you name your own tables.

Done when `from warehouse import query, execute` runs without an error. Then step 2.

### 2. See what a table says about itself

Goal: know where a Table reference's facts come from. A table in the warehouse can describe
itself. The Hive command DESCRIBE lists its columns and
their types, and SHOW PARTITIONS lists the Partitions it holds. Neither reads a single row, so
both are quick on the biggest table. Here is what DESCRIBE says of `ops.run_alerts`, sent
straight through your query:

>>> described = query("DESCRIBE ops.run_alerts")  # -> DataFrame
>>> described
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
section: its name is empty, and its other two cells are missing, NULL in Hive, which pandas
prints as NaN. The rows under `# Partition Information` say which columns split the table into
Partitions, the pieces the warehouse stores it in: here dt alone, one Partition for each value
of dt.

Done when `described` lists alert_id, run_id, severity and dt. Then step 3.

### 3. Write your tables' Table references

Goal: a Table reference for each table you read. `project.add_references` takes a list of
tables. For each, it sends those two commands through your query, turns what comes back into a
Table reference file in `references/`, and adds it to the registry, admin/registry.csv, the
list of what each Project action made; then it logs what it did in the Admin log, the record of
each Project action. It also proposes each table's Key, the columns that name one row: it
counts each id column's values, such as run_id's, on the latest Partition, then checks the one
that names every row with `check_key`, which step 9 shows, on the latest two Partitions. Run it
from the references Workflow's notebook, admin/workflows/references/references.ipynb, which
runs this call on the names in its names cell, or from any notebook in the Project's folder, as
here:

>>> project.add_references(["ops.jobs", "ops.job_runs", "ops.run_alerts"], query=query)
Wrote references/ops__jobs.py, references/ops__job_runs.py and references/ops__run_alerts.py:
    fill in their TODO lines.
ops.jobs: its Key proposed, (job_id), checked with check_key:
  ops.jobs: the key (job_id) holds.
ops.job_runs: its Key proposed, (run_id), checked with check_key:
  ops.job_runs: the key (run_id) holds where job_runs.dt IN ('2026-09-23', '2026-09-24').
ops.run_alerts: its Key proposed, (alert_id), checked with check_key:
  ops.run_alerts: the key (alert_id) holds where run_alerts.dt IN ('2026-09-23',
    '2026-09-24').
To accept every proposed Key, write in the decisions cell: "all_tables": {"key": "proposed"}
Wrote references/ops.py: from references import ops gives ops.job_runs, ops.jobs and
    ops.run_alerts.
Restart the kernel of a notebook that imported references, to see a table added since.

Its "fill in their TODO lines." means the lines it proposed nothing for: here only each
`key=None,  # TODO: proposed [...]` line, which step 5 accepts in the decisions cell, since a
Key proposed from a table's rows stays open until you do. A table it proposed no Key for has
one more, its first line, what one row is. Every other line it proposed is marked
`# proposed`, and blocks nothing.

Its "To accept every proposed Key" line is one line of the decisions cell. Run from the
references Workflow's "Run up to your Decisions", the run then stops at the Decisions and
prints the whole DECISIONS to paste over the cell's `DECISIONS = {}` line, that line inside it,
its comments shortened here:

    DECISIONS = {
        "all_tables": {  # answers for every table of this notebook
            "key": "proposed",  # accepts each table's proposed Key, as if typed
        },
    }

Each file is named after the database and the table joined by two underscores, `ops.jobs`
giving ops__jobs.py, since a dot can't be in a name Python imports. The variable in it is
named after the table alone, jobs.

The last file is the Database module of the Database ops, the first part of each table's name:
references/ops.py, which the Project actions write again each time a Table reference is added
or archived. Leave it as they write it.

Done when it says `Wrote references/ops__jobs.py` and `Wrote references/ops.py`. Then step 4.

### 4. Read a Table reference it wrote

Goal: know what the file holds and what it leaves to you. Open references/ops__job_runs.py in
your editor. It imports `Table`, then makes one variable, `job_runs`:

- `columns=` holds every column and its type;
- `partitioned_by=["dt"]` comes from DESCRIBE's `# Partition Information` rows;
- three lines are proposed, since the table can't say them for sure: the line at the top,
  what one row is, `"One row per run_id."  # proposed from its Key`; `does_not_add_up=`, the
  columns that are averages or ratios, `["avg_retry_secs"]  # proposed from its columns'
  names`, from names such as avg_*, *_ratio and *_rate; and the Key, `key=None,  # TODO:
  proposed ["run_id"], checked`, which stays open until you accept it. A table with no id
  column, or none naming every row, gets no Key proposed, and its line says why. A Key
  convert or new_table proposes, worked out of a table's query, such as its GROUP BY, is
  kept unless you answer it, since the query proves it; one proposed from a table's rows, as
  here, waits for your yes;
- `descriptions=` holds what each column holds, in words, from its comment in the warehouse,
  such as status's `SUCCESS / FAILED / TEST, NULL while running`;
- under the Aliases heading at the end, commented-out examples show how to add your own names
  for the table's columns and conditions.

Done when you have found the file's three proposed lines. Then step 5.

### 5. Accept or change what it proposed

Goal: a Table reference that says what only you know. A proposed Key waits for your yes, as
proof from a few Partitions is evidence, not a promise. In the references Workflow's notebook,
the decisions cell under "Run up to your Decisions" accepts it: `"key": "proposed"` under
"all_tables" accepts every table's, under a table's name that one's, and a Key of your own,
such as `{"ops.job_runs": {"key": ["run_id"]}}`, wins over it. "Run the rest" writes each in.
This page stands in for that cell and its step:

>>> DECISIONS = {"all_tables": {"key": "proposed"}}
>>> print(project.write_decisions(DECISIONS, tables=["ops.jobs", "ops.job_runs",
...                                                  "ops.run_alerts"]))
Wrote 1 answer into references/ops__jobs.py.
Each Decision of ops.jobs is made.
Wrote 1 answer into references/ops__job_runs.py.
Each Decision of ops.job_runs is made.
Wrote 1 answer into references/ops__run_alerts.py.
Each Decision of ops.run_alerts is made.
all_tables: key "proposed": accepted the proposed Key of ops.jobs, ops.job_runs and
    ops.run_alerts, each written as if typed.

The other two proposed lines are used as they are, blocking nothing; `project.check()` names
each one left. Keep each, taking off its `# proposed` comment, or change it: say in your own
words what one row is. This is references/ops__job_runs.py with them kept, its first line in
your own words, and two Aliases of your own at the end:

The file `references/ops__job_runs.py`, after you fill it in:

    \"\"\"ops.job_runs - one row per run of a job, on the day it ran.\"\"\"
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

    # --- Aliases ------------------------------------------------------------------------------
    # Your own names for this table's columns and conditions, written by hand below.
    # Import one beside the table: from references.ops__job_runs import job_runs, <alias>
    #
    # A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
    # get back, still call the column by its own name. To rename an output, use AS(...).
    #     <alias> = job_runs.status
    # A condition Alias names a condition on this table alone, for WHERE or
    # count_rows(where=...). Add what it calls, such as equals, to the import at the top.
    #     <alias> = equals(job_runs.status, <value>)

    minutes = job_runs.duration_mins
    failed = equals(job_runs.status, "FAILED")

- The first line says, in your own words, what one row is.
- `key=` lists the columns that pick out one row, the table's Key. Every run has its own
  `job_runs.run_id`, so it is `key=["run_id"]`, as the decisions cell wrote it. Ask whoever
  owns the table if you aren't sure: `check_key`, in step 9, checks a Key of your own. A join
  uses the Key to warn you when it would repeat rows.
- `does_not_add_up=` lists the columns that are averages, ratios or counts of different values.
  `job_runs.avg_retry_secs` is each run's average wait between retries: adding up two runs'
  averages gives a number that means nothing, so the Toolbox refuses to add it up once it is
  listed here. Its name said so, so it was proposed; a column whose name doesn't, such as a
  share, you add yourself.
- An Alias is your own name, written by hand. `minutes` is a shorter name for
  `job_runs.duration_mins`, for you: the Hive, and the DataFrame a query gives back, still call
  the column duration_mins. `failed` names a condition on this table alone. Add `equals` to the
  import at the top, beside `Table`, since `failed` calls it.
- `descriptions=` is yours too: add what a column holds where the warehouse has no comment, as
  `"duration_mins": "how long the run took, in minutes"`.

The other two the same way. A job is one row of ops.jobs, and nothing in it is an average, so
its proposed `does_not_add_up=[]` stays empty; the `# proposed` comments go:

The file `references/ops__jobs.py`, after you fill it in:

    \"\"\"ops.jobs - one row per job: its name, the team that owns it and its region.\"\"\"
    from sqlglot_composer import Table

    jobs = Table(
        "ops.jobs",
        columns={
            "job_id": "bigint",
            "job_name": "string",
            "team": "string",
            "region": "string",
        },
        key=["job_id"],
        does_not_add_up=[],
    )

    # --- Aliases ------------------------------------------------------------------------------
    # Your own names for this table's columns and conditions, written by hand below.
    # Import one beside the table: from references.ops__jobs import jobs, <alias>
    #
    # A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
    # get back, still call the column by its own name. To rename an output, use AS(...).
    #     <alias> = jobs.job_name
    # A condition Alias names a condition on this table alone, for WHERE or
    # count_rows(where=...). Add what it calls, such as equals, to the import at the top.
    #     <alias> = equals(jobs.job_name, <value>)

A run can raise several alerts, so the Key of ops.run_alerts is its alert_id, not its
run_id. It gets an Alias too, high, for its high alerts:

The file `references/ops__run_alerts.py`, after you fill it in:

    \"\"\"ops.run_alerts - one row per alert a run raised.\"\"\"
    from sqlglot_composer import Table, equals

    run_alerts = Table(
        "ops.run_alerts",
        columns={
            "alert_id": "bigint",
            "run_id": "bigint",
            "severity": "string",
            "dt": "string",
        },
        partitioned_by=["dt"],
        key=["alert_id"],
        does_not_add_up=[],
        descriptions={
            "severity": "low / high",
        },
    )

    # --- Aliases ------------------------------------------------------------------------------
    # Your own names for this table's columns and conditions, written by hand below.
    # Import one beside the table: from references.ops__run_alerts import run_alerts, <alias>
    #
    # A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
    # get back, still call the column by its own name. To rename an output, use AS(...).
    #     <alias> = run_alerts.severity
    # A condition Alias names a condition on this table alone, for WHERE or
    # count_rows(where=...). Add what it calls, such as equals, to the import at the top.
    #     <alias> = equals(run_alerts.severity, <value>)

    high = equals(run_alerts.severity, "high")

Done when each table's Key is accepted or your own, so no file holds a
`key=None,  # TODO` line. Keeping or changing each `# proposed` line, and adding Aliases, is
yours to do when you like: they block nothing. Then step 6.

### 6. Reach a table and its columns

Goal: each table and column by name, in any notebook. In any notebook of the Project, one line
imports the Database module, and with it every table of the Database ops:

>>> from references import ops

Each table is at a dot after `ops`, and each of its columns at a dot after the table. In a
notebook, tab completion lists them at each dot:

>>> ops.job_runs  # -> Table
Table('ops.job_runs', columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt)
>>> ops.job_runs.status  # -> Column
job_runs.status

A Column is what the Toolbox's functions take, as you'll see in
[Build and run a first statement](#build_and_run_a_first_statement). In an f-string, a Column
gives the name the Hive knows it by, and a Table what follows FROM, for the rare Hive you write
by hand
([Hand-written Hive with your Table references](#hand_written_hive_with_your_table_references)
shows when):

>>> f"WHERE {ops.job_runs.status} = 'FAILED'"  # -> str
"WHERE job_runs.status = 'FAILED'"
>>> f"FROM {ops.job_runs}"  # -> str
'FROM ops.job_runs AS job_runs'

Done when `ops.job_runs.status` shows `job_runs.status`. Then step 7.

### 7. Import an Alias from its table's file

Goal: your own names in a notebook. `ops` gives each table, but not your Aliases: they are
names in the table's own file. Import them from it, by its name in `references/`, beside the
table:

>>> from references.ops__job_runs import job_runs, failed, minutes
>>> minutes  # -> Column
job_runs.duration_mins
>>> failed  # -> Condition
job_runs.status = 'FAILED'

`job_runs` is the same Table as `ops.job_runs`. Import a table from its own file when you use
its Aliases, as the Building blocks and Table notebooks after this how-to do; otherwise
`from references import ops` is all a notebook needs.

Done when `minutes` shows `job_runs.duration_mins`. Then step 8.

### 8. Check each file against its table

Goal: a file that still says what the table holds. `check_table_reference` asks the table for
its columns again and compares them with the file. Run it after you edit a Table reference, and
whenever the table may have changed:

>>> check_table_reference(ops.job_runs, query=query)  # -> Verdict
ops.job_runs matches its Table reference.

It gives back a Verdict: what the check found, which prints as the sentence above, and whose
`.ok` is True when it found nothing wrong. When something differs, it lists each problem with
the line to change in the file. It leaves the file for you to edit.

Done when it says `ops.job_runs matches its Table reference.` Then step 9.

### 9. Check a Key again

Goal: proof that the Key names one row. The warehouse never checks a Key: nothing stops two
rows sharing one run_id. `check_key`, which step 3 ran on each proposed Key, counts the rows
for each Key, and lists any Key that repeats. Run it on a Key of your own, and again whenever
the table may have changed. ops.job_runs is partitioned, so
`where=` says which Partitions to check, here those whose dt is 2026-09-24; a table that isn't
partitioned, such as ops.jobs, is checked whole:

>>> check_key(ops.job_runs, query=query,
...           where=equals(ops.job_runs.dt, "2026-09-24"))  # -> Verdict
ops.job_runs: the key (run_id) holds where job_runs.dt = '2026-09-24'.
>>> check_key(ops.jobs, query=query)  # -> Verdict
ops.jobs: the key (job_id) holds.

`reads_all_partitions=True` in place of `where=` checks the whole of a partitioned table.

Done when each check says its key holds. Then check it worked, below.

## Check it worked

The three Table reference files and the Database module are in references/, and the registry
lists each Table reference:

>>> from pathlib import Path
>>> sorted(path.name for path in Path("references").glob("ops*.py"))
['ops.py', 'ops__job_runs.py', 'ops__jobs.py', 'ops__run_alerts.py']
>>> project.check()
Every Table folder, Table reference and Building block is registered, and each one registered is
    there.

Each file matches its table:

>>> for table in (ops.jobs, ops.job_runs, ops.run_alerts):
...     print(check_table_reference(table, query=query))
ops.jobs matches its Table reference.
ops.job_runs matches its Table reference.
ops.run_alerts matches its Table reference.

Before you go on, check that:

- references/ holds ops.py, ops__job_runs.py, ops__jobs.py and ops__run_alerts.py;
- `project.check()` says every Table reference is registered;
- `check_table_reference` says each table matches its Table reference;
- `check_key` says each Key holds.

## Common mistakes

### A column name the table doesn't have

A Table reference is there so you reach each column by name, never typing it as text. Use tab
completion at the dot to pick the name. A misspelt column stops
the line it is on, and lists the columns the table has:

>>> ops.job_runs.stauts
Traceback (most recent call last):
...
AttributeError: job_runs has no column 'stauts'. Did you mean 'status'? Its columns are: run_id,
    job_id, status, duration_mins, avg_retry_secs, dt.

A misspelt table stops the same way, and lists the tables of the Database:

>>> ops.job_run
Traceback (most recent call last):
...
AttributeError: ops has no table 'job_run'. Did you mean 'job_runs'? Its tables are: job_runs,
    jobs, run_alerts.

### Reaching an Alias through ops

An Alias isn't a column of the table, so `ops` can't give it:

>>> ops.job_runs.failed
Traceback (most recent call last):
...
AttributeError: job_runs has no column 'failed'. Its columns are: run_id, job_id, status,
    duration_mins, avg_retry_secs, dt.

Import it from the table's file: `from references.ops__job_runs import failed`.

### Adding a table whose Table reference is already there

`project.add_references` writes over no file: once written, the file is yours, and writing it
again would lose the Key and the notes you added. A list that names a table already
in `references/` writes the others, skips that one, and then stops, naming it:

>>> project.add_references(["ops.jobs"], query=query)
Traceback (most recent call last):
...
sqlglot_composer.project.SkippedTables:
  What happened:  add_references skipped 1 of 1 tables: ops.jobs (references/ops__jobs.py is
                  there already).
...

For a table whose file is there, edit the file instead, and run
`check_table_reference` to see what has changed in the table since.

### A table added after the notebook imported references

A notebook that ran `from references import ops` keeps the tables ops had then. After
`project.add_references` adds another, restart the notebook's kernel, as its last line says,
and run the import again: `ops` then gives the new table too.

## Next

- Build a Statement on these tables, read its Hive and run it:
  [Build and run a first statement](#build_and_run_a_first_statement).
- Describe a table that doesn't exist yet, by hand:
  [Describe a table by hand](#describe_a_table_by_hand).
- Read every column of the Project's tables in one place, and check every Table reference at
  once: [Keep the Project in order](#keep_the_project_in_order).
- Each function here has a Worked example in the gallery:
  [`write_table_reference`](examples.html#write_table_reference), which writes one table's
  file, [`check_table_reference`](examples.html#check_table_reference) and
  [`check_key`](examples.html#check_key).
"""
