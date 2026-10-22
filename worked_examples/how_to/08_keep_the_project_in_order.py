"""Keep the Project in order

For: Getting started

## Goal

Keep your Project's files and its tables in step as they change. The registry lists every
Table folder, Table reference and Building block a Project action made: `project.check()`
says what it gets wrong, and `project.register` adopts a file made by hand. The Reference
sheet lists every column of every table in one CSV file. admin/check_references.ipynb compares
each Table reference with its table in the warehouse. The `project.remove_*` actions archive
what you no longer need, deleting nothing. And the Levels say which of your files may import
which.

## When you'd use it

- After you copy in a file by hand, such as a colleague's Table reference, or move or delete
  one.
- When you look for a column and don't know which table has it, or someone new asks what the
  Project's tables hold.
- On a schedule, say every Monday, and whenever a table's owners say it changed: a table goes
  on changing after its Table reference is written, and a Table reference out of date lets
  through Statements the warehouse then refuses.
- When a Saved table, a Table reference or a Building block is no longer needed.

## Steps

### Where the last how-to left the Project

[Follow lineage](#follow_lineage) left the Project with its Table references, its Building
block and its Saved tables. This how-to looks at the Project's files rather than
running its notebooks, so the steps make it again with the three Table references filled in,
the Building block as `project.new_block` writes it, and one Saved table,
mart.alerts_per_severity, whose Table reference is filled in:

>>> import csv
>>> import os
>>> from pathlib import Path
>>> import pandas as pd
>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/ and warehouse.py.
Next: write your two functions, query and execute, in warehouse.py.
>>> from warehouse import query, execute
>>> project.add_references(["ops.jobs", "ops.job_runs", "ops.run_alerts"], query=query)
Wrote references/ops__jobs.py, references/ops__job_runs.py and references/ops__run_alerts.py: fill in their TODO lines.
Wrote references/ops.py: from references import ops gives ops.job_runs, ops.jobs and ops.run_alerts.
Restart the kernel of a notebook that imported references, to see a table added since.
>>> project.new_block("runs_per_job")
Wrote building_blocks/runs_per_job.py, from admin/templates/building_block.py:
fill in its <...> and TODO lines.
>>> project.new_table("mart.alerts_per_severity")
Made tables/mart__alerts_per_severity/: mart__alerts_per_severity.ipynb and lineage/, from
admin/templates/saved_table.py.
Wrote references/mart__alerts_per_severity.py: fill in its <...> and TODO lines.

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

### Read the registry, and check it

Each Project action adds a row to the registry, admin/registry.csv: what it made, the table or
Building block, when, and, once it is archived, when that was. You never edit it; the Project
actions do:

>>> registry = pd.read_csv("admin/registry.csv", keep_default_na=False)  # -> DataFrame
>>> registry[["kind", "table", "removed_at"]]
             kind                     table removed_at
0       reference                  ops.jobs
1       reference              ops.job_runs
2       reference            ops.run_alerts
3  building_block              runs_per_job
4    table_folder  mart.alerts_per_severity
5       reference  mart.alerts_per_severity

`project.check()`, which the admin notebook admin/check_project.ipynb runs, compares the
registry with the files, and changes nothing:

>>> project.check()
Every Table folder, Table reference and Building block is registered, and each one registered is there.

### Adopt a file made by hand with project.register

Say a colleague gives you the Table reference they wrote for `ops.scheduler_runs`, and you copy
it into references/:

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
Wrote references/ops.py: from references import ops gives ops.job_runs, ops.jobs, ops.run_alerts and ops.scheduler_runs.
Restart the kernel of a notebook that imported references, to see a table added since.

`project.register` takes a table's name, with its database, for its Table folder or Table reference,
and a Building block's name, with no dot, such as `project.register("runs_per_job")`, for its
file in building_blocks/. It also wrote the Database modules again, so `from references import
ops` now gives `ops.scheduler_runs` too.

### Keep each file to its Level

Your files sit at three Levels, and a file imports only from the Toolbox and from Levels below
its own, never from its own Level or one above:

| Level | Files | May import |
|---|---|---|
| 0 | references/: each Table reference and Database module; warehouse.py | the Toolbox; a Database module also imports the Table references of its Database |
| 1 | building_blocks/: each Building block | the Toolbox and Level 0 |
| 2 | each Table notebook's logic cell | the Toolbox, Level 0 and Level 1 |

What runs many Table notebooks in order, such as admin/run_tables.ipynb, sits above the three,
and may read them all. So a Table reference never imports a Building block, and a Building
block never imports another: a block that reads another takes the Derived table it gives back
as an argument, from the notebook that imports both, as [Share Building
blocks](#share_building_blocks) says. A file changed at one Level then never breaks one below
it, and `project.load` can run any notebook's logic from anywhere in the Project. Nothing
stops an import that breaks the Levels: keep to them as you write.

### Read the Reference sheet

`project.refresh_reference_sheet()`, from admin/refresh_reference_sheet.ipynb, writes
references/reference_sheet.csv from the Table references in references/, never from the
warehouse, so it says what your files say:

>>> project.refresh_reference_sheet()
Wrote references/reference_sheet.csv: 20 rows, 5 tables.

It has a row per column of each table: the table and the column, its Hive type, "yes" under
partition and in_key for each partition column and each column of the Key, its Aliases (a
condition shown as "failed (a condition)"), its description, and exported_at, when the sheet
was written. Read it in a spreadsheet, or in pandas. Python's `csv` module keeps an empty cell
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

### Check each Table reference against its table

admin/check_references.ipynb compares every table the Reference sheet lists with the table in
the warehouse, through your query: DESCRIBE lists the table's columns, their types and its
partition columns, and never its rows. It prints what differs, with the line to change, then
checks each Key it can. Run it in Jupyter, top to bottom. At its heart is
`check_table_reference`, which gives back a Verdict; here, on each Table reference, with the
Project's query from warehouse.py:

>>> from references import mart, ops
>>> for table in [ops.jobs, ops.job_runs, ops.run_alerts, mart.alerts_per_severity]:
...     print(check_table_reference(table, query=query))
ops.jobs matches its Table reference.
ops.job_runs matches its Table reference.
ops.run_alerts matches its Table reference.
mart.alerts_per_severity: DESCRIBE FORMATTED failed, so nothing was compared. Check the table's name, and that your query works. It said:
    ValueError:
    What happened:  The Example database has no table 'mart.alerts_per_severity'.
    Why it matters: It holds nine made-up tables, all in the database ops.
    Usual fix:      Use ops.jobs, ops.job_runs, ops.run_alerts, ops.scheduler_runs, ops.job_events, ops.job_owners, ops.region_costs, ops.region_budgets or ops.team_notes.
    Opt-out:        none - this one can't be switched off.

The Saved table reports that DESCRIBE failed: it exists only once its notebook's create() has
made it in your warehouse, and the Example database holds none, so that is expected here, as
the notebook reports for each Saved table of the Starter Example project. At work, a Saved
table you have created is compared like the others.

When a table changes under its Table reference, the check says how. Say the team that owns
`ops.jobs` adds a column, `"owner"`. A stand-in query plays the warehouse after that change: it
answers DESCRIBE with the new columns, and passes every other query on:

>>> def query_after_the_change(hive: str) -> pd.DataFrame:  # -> DataFrame
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
line it gives into the Table reference. The check never edits your file. Then refresh the
table's rows in the Reference sheet.

### Archive what you no longer need

Say you made a Table folder for mart.job_minutes, and then found mart.daily_job_runs holds its
numbers already:

>>> project.new_table("mart.job_minutes")
Made tables/mart__job_minutes/: mart__job_minutes.ipynb and lineage/, from
admin/templates/saved_table.py.
Wrote references/mart__job_minutes.py: fill in its <...> and TODO lines.

`project.remove_table`, from admin/remove_table.ipynb, moves the Table folder, whole, into
admin/removed/, named by the time, and marks its registry row removed.
`project.remove_reference` then archives its Table reference the same way:

>>> project.remove_table("mart.job_minutes")  # the time it ran, as yyyymmdd-hhmmss
Moved tables/mart__job_minutes/ to admin/removed/...-mart__job_minutes/.
>>> project.remove_reference("mart.job_minutes")
Moved references/mart__job_minutes.py to admin/removed/...-mart__job_minutes.py.

Nothing is deleted, and nothing in the warehouse changes: a table you created stays there until
you drop it with an Admin statement, a Statement that changes one of your Saved tables in the
warehouse, such as dropping it. The admin module makes them; import it by name, since the star
import leaves it out:

>>> from sqlglot_composer import admin

`admin.drop_table(...)` gives the one that drops a table, which you send with
`run(..., execute=execute)`, as admin/change_a_saved_table.ipynb does. `help(admin)` lists
every Admin statement.

`project.remove_block` archives a Building block the same way, from admin/new_block.ipynb's
last cell. Each refuses while something still needs what it archives:
`project.remove_reference` while the table has a Table folder, whose notebook imports it, and
`project.remove_block` while a Table notebook or another Building block imports the block,
naming each.

## Check it worked

The registry lists the archived table and reference as removed, and `project.check()` finds
nothing amiss:

>>> registry = pd.read_csv("admin/registry.csv", keep_default_na=False)  # -> DataFrame
>>> registry[registry.removed_at != ""][["kind", "table"]]
           kind              table
7  table_folder  mart.job_minutes
8     reference  mart.job_minutes
>>> project.check()
Every Table folder, Table reference and Building block is registered, and each one registered is there.

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
"""
