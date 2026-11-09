"""Keep the Project in order

For: Getting started

## Goal

Keep your Project's files and its tables in step as they change. A Project is your folder of
scripts at work, in the Toolbox's fixed layout, and a Project action is a one-time change to
its files, such as `project.new_table`. The registry is the Project's list of every Table
folder, Table reference, Building block and Conversion folder a Project action made:
`project.check()` says what it gets wrong, and `project.register` adopts a file made by hand.
A Table reference is the file that describes one table; a Table folder holds everything about
one Saved table, a table your Statements write; a Building block is a piece of your own code
reused across notebooks. The Reference sheet lists every column of every table in one CSV file.
admin/check_references.ipynb compares each Table reference with its table in the warehouse. The
`project.remove_*` actions archive what you no longer need, deleting nothing. And the Levels,
the three tiers of your own files, say which of your files may import which.

## When you'd use it

- If you copy in a file by hand, such as a colleague's Table reference, run `project.check()`
  and adopt it with `project.register` (steps 3 and 4).
- If you move or delete a file by hand, run `project.check()`: it says the call that mends the
  registry.
- If you look for a column and don't know which table has it, or someone new asks what the
  Project's tables hold, read the Reference sheet (steps 6 and 7).
- If a table's owners say it changed, or on a schedule, say every Monday, check each Table
  reference against its table (steps 8 and 9): a table goes on changing after its Table
  reference is written, and a Table reference out of date lets through Statements the
  warehouse then refuses.
- If a Saved table, a Table reference or a Building block is no longer needed, archive it
  (step 10).

## Steps

### 1. Set up the Project the last how-to left

Goal: a Project with Table references, a Building block and a Saved table to keep in order.

[Follow lineage](#follow_lineage) left the Project with its Table references, its Building
block and its Saved tables. This how-to looks at the Project's files rather than running its
notebooks, so the calls below make it again with the three Table references filled in, the
Building block as `project.new_block` writes it, and one Saved table,
mart.alerts_per_severity, whose Table reference is filled in:

>>> import csv
>>> import os
>>> from pathlib import Path
>>> import pandas as pd
>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/, scheduled_runs/ and warehouse.py.
Next: at the top of each notebook, fill in connect(...) with your connection.
>>> from warehouse import connect, query, execute
>>> connect(example_database)
>>> project.add_references(["ops.jobs", "ops.job_runs", "ops.run_alerts"], query=query)
Wrote references/ops__jobs.py, references/ops__job_runs.py and references/ops__run_alerts.py:
    fill in their TODO lines.
...
Wrote references/ops.py: from references import ops gives ops.job_runs, ops.jobs and
    ops.run_alerts.
Restart the kernel of a notebook that imported references, to see a table added since.
>>> project.new_block("runs_per_job")
Wrote building_blocks/runs_per_job.py, from admin/templates/building_block.py:
fill in its <...> and TODO lines.
>>> project.new_table("mart.alerts_per_severity")
Made tables/mart__alerts_per_severity/: mart__alerts_per_severity.ipynb and lineage/, from
admin/templates/saved_table.py.
Wrote references/mart__alerts_per_severity.py: project.reference_from_logic writes it.

The file `references/ops__jobs.py`, after you fill it in:

    \"\"\"ops.jobs - one row per job: its name, the team that owns it and its region.\"\"\"
    from sqlglot_composer import Table

    jobs = Table(
        "ops.jobs",
        columns={"job_id": "bigint", "job_name": "string", "team": "string", "region": "string"},
        key=["job_id"],
        does_not_add_up=[],
    )

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
        descriptions={"status": "SUCCESS / FAILED / TEST, NULL while running"},
    )

    minutes = job_runs.duration_mins
    failed = equals(job_runs.status, "FAILED")

The file `references/ops__run_alerts.py`, after you fill it in:

    \"\"\"ops.run_alerts - one row per alert a run raised.\"\"\"
    from sqlglot_composer import Table, equals

    run_alerts = Table(
        "ops.run_alerts",
        columns={"alert_id": "bigint", "run_id": "bigint", "severity": "string", "dt": "string"},
        partitioned_by=["dt"],
        key=["alert_id"],
        does_not_add_up=[],
        descriptions={"severity": "low / high"},
    )

    high = equals(run_alerts.severity, "high")

The file `references/mart__alerts_per_severity.py`, after you fill it in:

    \"\"\"mart.alerts_per_severity - one row per severity and day: the alerts raised.\"\"\"

    from sqlglot_composer import Table

    alerts_per_severity = Table(
        "mart.alerts_per_severity",
        columns={"severity": "string", "alerts": "bigint", "dt": "string"},
        partitioned_by=["dt"],
        key=["severity", "dt"],
        location="/data/your_team/mart.db/alerts_per_severity",
    )

Done when the four Table references are filled in as shown. Then step 2.

### 2. Read the registry

Goal: what each Project action made. Each Project action adds a row to the registry,
admin/registry.csv: what it made, the table or Building block, when, and, once it is archived,
when that was. The Project actions write it; leave it to them:

>>> registry = pd.read_csv("admin/registry.csv", keep_default_na=False)  # -> DataFrame
>>> registry[["kind", "table", "removed_at"]]
             kind                     table removed_at
0       reference                  ops.jobs
1       reference              ops.job_runs
2       reference            ops.run_alerts
3  building_block              runs_per_job
4    table_folder  mart.alerts_per_severity
5       reference  mart.alerts_per_severity

Done when the registry has six rows, none removed. Then step 3.

### 3. Check the registry against the files

Goal: know whether the registry and the files agree. `project.check()`, which the admin
notebook admin/check_project.ipynb runs, compares the registry with the files, and changes
nothing:

>>> project.check()
Every Table folder, Table reference and Building block is registered, and each one registered is
    there.

Done when it says every one is registered and there. Then step 4.

### 4. Adopt a file made by hand with project.register

Goal: a file made by hand listed in the registry. Say a colleague gives you the Table reference
they wrote for `ops.scheduler_runs`, and you copy it into references/:

The file `references/ops__scheduler_runs.py`, after you copy it in:

    \"\"\"ops.scheduler_runs - one row per run the scheduler started.\"\"\"
    from sqlglot_composer import Table

    scheduler_runs = Table(
        "ops.scheduler_runs",
        columns={"run_id": "bigint", "job_id": "bigint", "dt": "string"},
        partitioned_by=["dt"],
        key=["run_id"],
    )

No Project action made it, so the registry doesn't list it, and `project.check()` says so, with
the call that mends it:

>>> project.check()
Not registered, made by hand. Adopt each with the call beside it:
  references/ops__scheduler_runs.py: project.register("ops.scheduler_runs")
>>> project.register("ops.scheduler_runs")
Registered references/ops__scheduler_runs.py.
Wrote references/mart.py: from references import mart gives mart.alerts_per_severity.
Wrote references/ops.py: from references import ops gives ops.job_runs, ops.jobs, ops.run_alerts
    and ops.scheduler_runs.
Restart the kernel of a notebook that imported references, to see a table added since.

`project.register` takes a table's name, with its database, for its Table folder or Table
reference, and a Building block's name, with no dot, such as `project.register("runs_per_job")`,
for its file in building_blocks/. It also wrote the Database modules again, so
`from references import ops` now gives `ops.scheduler_runs` too. A Database module, such as
references/ops.py, is the one file that gives each table of a Database, the first part of a
table's name, `ops` in `ops.jobs`.

Done when it says `Registered references/ops__scheduler_runs.py.` Then step 5.

### 5. Keep each file to its Level

Goal: imports that never break a file at a lower Level. Your files sit at three Levels, and a
file imports only from the Toolbox and from Levels below its own:

- Level 0, references/, each Table reference and Database module, and warehouse.py: imports
  the Toolbox; a Database module also imports the Table references of its Database;
- Level 1, building_blocks/, each Building block: imports the Toolbox and Level 0;
- Level 2, each Table notebook's logic cell: imports the Toolbox, Level 0 and Level 1.

What runs many Table notebooks in order, such as admin/run_tables.ipynb, sits above the three,
and may read them all. So a Table reference imports no Building block, and a Building block
imports no other: a block that reads another takes the Derived table it gives back as an
argument, from the notebook that imports both, as [Share Building
blocks](#share_building_blocks) says. A Derived table is a Statement given a name so another
Statement can read from it. A file changed at one Level then never breaks one below it, and
`project.load` can run any notebook's logic from anywhere in the Project. Nothing stops an
import that breaks the Levels: keep to them as you write.

Done when each file you write imports only from the Toolbox and from Levels below its own. Then
step 6.

### 6. Write the Reference sheet

Goal: references/reference_sheet.csv, written from your Table references.
`project.refresh_reference_sheet()`, from admin/refresh_reference_sheet.ipynb, writes
references/reference_sheet.csv from the Table references in references/, never from the
warehouse, so it says what your files say:

>>> project.refresh_reference_sheet()
Wrote references/reference_sheet.csv: 20 rows, 5 tables.

Done when it says it wrote 20 rows, 5 tables. Then step 7.

### 7. Read the Reference sheet

Goal: find a column, and the tables that have it. The sheet has a row per column of each
table: the table and the column, its Hive type, "yes" under
partition and in_key for each partition column and each column of the Key, the columns whose
values name one row, its Aliases, the names you give a column or a condition in a Table
reference (a condition shown as "failed (a condition)"), its description, and exported_at,
when the sheet was written. Read it in a spreadsheet, or in pandas. Python's `csv` module keeps an empty cell
as empty text, `""`, so `sheet.aliases != ""` picks the filled ones:

>>> with open("references/reference_sheet.csv", encoding="utf-8", newline="") as file:
...     sheet = pd.DataFrame(csv.DictReader(file))  # -> DataFrame

Every table with a column named job_id, to see where a join on it could go:

>>> sheet[sheet.column == "job_id"][["table", "type", "in_key"]]
                 table    type in_key
4         ops.job_runs  bigint
9             ops.jobs  bigint    yes
18  ops.scheduler_runs  bigint

Every Alias, and the column it reads:

>>> sheet[sheet.aliases != ""][["table", "column", "aliases"]]
             table         column               aliases
5     ops.job_runs         status  failed (a condition)
6     ops.job_runs  duration_mins               minutes
15  ops.run_alerts       severity    high (a condition)

After you change one Table reference, `project.refresh_reference_sheet("ops.job_runs")`
refreshes its rows alone, as a Table notebook's last cell does for its own table.

Done when you have the three tables with a job_id column, and the three Aliases. Then step 8.

### 8. Check each Table reference against its table

Goal: know whether each Table reference still matches its table in the warehouse.
admin/check_references.ipynb compares every table the Reference sheet lists with the table in
the warehouse, through your query: DESCRIBE FORMATTED, Hive's fuller DESCRIBE, lists the
table's columns, their types and its partition columns, and never its rows. It prints what
differs, with the line to change, then checks each Key it can. Run it in Jupyter, top to
bottom. At its heart is `check_table_reference`, which gives back a Verdict, whose `.ok` says
whether the check found nothing wrong; here, on each Table reference, with the Project's query
from warehouse.py:

>>> from references import mart, ops
>>> for table in [ops.jobs, ops.job_runs, ops.run_alerts, mart.alerts_per_severity]:
...     print(check_table_reference(table, query=query))
ops.jobs matches its Table reference.
ops.job_runs matches its Table reference.
ops.run_alerts matches its Table reference.
mart.alerts_per_severity: DESCRIBE FORMATTED failed, so nothing was compared. Check the table's
    name, and that your query works. It said:
    ValueError:
    What happened:  The Example database has no table 'mart.alerts_per_severity'.
    Why it matters: It holds nine made-up tables, all in the database ops.
    Usual fix:      Use ops.jobs, ops.job_runs, ops.run_alerts, ops.scheduler_runs,
                    ops.job_events, ops.job_owners, ops.region_costs, ops.region_budgets or
                    ops.team_notes.
    Opt-out:        none - this one can't be switched off.

The Saved table reports that DESCRIBE FORMATTED failed: it exists only once its notebook's
create() has made it in your warehouse, and the Example database, the small made-up tables
this page runs on, holds none, so that is expected here, as the notebook reports for each
Saved table of the Starter Example project. At work, a Saved table you have created is
compared like the others.

Done when each table the warehouse holds says it matches its Table reference. Then step 9.

### 9. Read what the check says when a table changes

Goal: the line to add or change when a table changes under its Table reference. Say the team
that owns `ops.jobs` adds a column, `"owner"`. A stand-in query plays the warehouse after that
change: it answers DESCRIBE FORMATTED with the new columns, and passes every other query on:

>>> def query_after_the_change(hive: str) -> pd.DataFrame:
...     if hive.startswith("DESCRIBE"):
...         return pd.DataFrame(
...             [("job_id", "bigint", ""), ("job_name", "string", ""), ("team", "string", ""),
...              ("region", "string", ""), ("owner", "string", "")],
...             columns=["col_name", "data_type", "comment"])
...     return query(hive)
>>> check_table_reference(ops.jobs, query=query_after_the_change)  # -> Verdict
ops.jobs matches its Table reference.
Notes:
  - owner is in the table but not in the Table reference: add "owner": "string", if you want it.

It still matches, since a Note may not matter: a column the Table reference doesn't list is
just not there for your Statements. A Problem, listed under Problems, such as a column gone or
a type changed, makes Statements wrong or the warehouse refuse them: fix every one, writing the
line it gives into the Table reference. The check leaves your file as it is, so you write the
line. Then refresh the table's rows in the Reference sheet.

- If the check lists a Note, add the line it gives if you want the column; your Statements
  stay right either way.
- If the check lists a Problem, write the line it gives into the Table reference, then refresh
  the table's rows in the Reference sheet.

Done when the check lists the Note about owner. Then step 10.

### 10. Archive what you no longer need

Goal: a Table folder and its Table reference moved to admin/removed/, nothing deleted. Say you
made a Table folder for mart.job_minutes, and then found mart.daily_job_runs holds its numbers
already:

>>> project.new_table("mart.job_minutes")
Made tables/mart__job_minutes/: mart__job_minutes.ipynb and lineage/, from
admin/templates/saved_table.py.
Wrote references/mart__job_minutes.py: project.reference_from_logic writes it.

`project.remove_table`, from admin/remove.ipynb, moves the Table folder, whole, into
admin/removed/, named by the time, and marks its registry row removed.
`project.remove_reference` then archives its Table reference the same way:

>>> project.remove_table("mart.job_minutes")  # the time it ran, as yyyymmdd-hhmmss
Moved tables/mart__job_minutes/ to admin/removed/...-mart__job_minutes/.
>>> project.remove_reference("mart.job_minutes")
Moved references/mart__job_minutes.py to admin/removed/...-mart__job_minutes.py.

`project.remove_block` archives a Building block the same way, from admin/remove.ipynb. Each
refuses while something still needs what it archives: `project.remove_reference` while the
table has a Table folder, whose notebook imports it, and `project.remove_block` while a Table
notebook or another Building block imports the block, naming each. So archive the Table folder
first, then its Table reference, as here.

Done when both are moved to admin/removed/. Then step 11.

### 11. Drop a table you created, with an Admin statement

Goal: a table you created gone from the warehouse, once you mean it. Nothing is deleted, and
nothing in the warehouse changes: a table you created stays there until you drop it with an
Admin statement, a Statement that changes one of your Saved tables in the warehouse, such as
dropping it. The admin module makes them; import it by name, since the star import leaves it
out:

>>> from sqlglot_composer import admin

`admin.drop_table(...)` gives the one that drops a table, which you send with
`run_execute(..., execute)`, as
admin/workflows/change_a_saved_table/change_a_saved_table.ipynb does. `help(admin)` lists
every Admin statement.

Done when `from sqlglot_composer import admin` runs; this page drops nothing, since
mart.job_minutes was never created. Then check it worked, below.

## Check it worked

The registry lists the archived table and reference as removed, and `project.check()` finds
nothing amiss:

>>> registry = pd.read_csv("admin/registry.csv", keep_default_na=False)  # -> DataFrame
>>> registry[registry.removed_at != ""][["kind", "table"]]
           kind              table
7  table_folder  mart.job_minutes
8     reference  mart.job_minutes
>>> project.check()
Every Table folder, Table reference and Building block is registered, and each one registered is
    there.

Before you go on, check that:

- the registry marks mart.job_minutes' Table folder and Table reference removed;
- `project.check()` says every one is registered and there;
- references/reference_sheet.csv lists ops.scheduler_runs, the file you adopted;
- admin/removed/ holds mart__job_minutes' folder and file.

## Common mistakes

### Deleting a Table folder by hand

A folder deleted or moved by hand is still in the registry. `project.check()` says so, with the
call that marks it removed:

>>> import shutil
>>> shutil.rmtree("tables/mart__alerts_per_severity")
>>> project.check()
Registered, but not there. Put each back, or mark it removed with the call beside it:
  tables/mart__alerts_per_severity/: project.remove_table("mart.alerts_per_severity")
>>> project.remove_table("mart.alerts_per_severity")
tables/mart__alerts_per_severity/ wasn't there, so only its registry row is marked removed.

Archive with `project.remove_table` instead of deleting by hand: it keeps the notebook and its
Lineage in admin/removed/, where you can find them again.

### Deleting an admin notebook by mistake

`project.start()`, run again in the Project's folder, adds back only what start() makes and
the Project is missing, and writes over nothing:

>>> os.remove("admin/new_block.ipynb")
>>> project.start()
This folder is a Project already. Added what it lacked: admin/new_block.ipynb.

It does the same after you copy in a newer sqlglot_composer folder, adding the admin notebooks
and Templates it ships that your Project doesn't have yet.

### Editing the Reference sheet by hand

Each refresh writes the sheet again from the Table references, so a change typed into the CSV
file is gone the next time. Write a description in the Table reference's `descriptions={...}`,
and an Alias below its Table(...) call, then refresh: the file is where it lives, and the sheet
only shows it.

## Next

- Start the Intermediate how-tos, from the Intermediate Example project, such as [Rewrite some
  partitions](#rewrite_some_partitions).
- Move a Saved table that shares its folder: [Move a Saved table to its own
  folder](#move_a_saved_table_to_its_own_folder).
- The gallery's [`check_table_reference`](examples.html#check_table_reference) and
  [`check_key`](examples.html#check_key) entries.
"""  # noqa: E501 - a Levels table row, and the files it writes, byte for byte
