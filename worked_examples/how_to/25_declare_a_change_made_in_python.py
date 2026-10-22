"""Declare a change made in Python

For: Intermediate

## Goal

Change some rows in pandas, in a function of your own, save them to a table with your own
call, and declare the change to the Toolbox with `python_step`, so the Lineage of your tables
shows where the change lives, rather than stopping at the gap, and `project.run_tables` writes
the tables that read it after it.

## When you'd use it

When a step is easier in pandas than in a Statement. Here it is how many minutes longer each
run took than its job's usual run, the median, which pandas works out in one line. The
Toolbox never moves the rows: you pull them with a Statement, change them with your function,
and save them with your work's own call. `python_step` only tells the Toolbox which columns the
change read, which table it wrote, and which function made it, so whoever reads the Lineage
can open that function and see what it does.

It needs [Save a table](#save_a_table), [Share Building blocks](#share_building_blocks) and
[Follow Lineage](#follow_lineage).

## Steps

### Start from the Intermediate Example project

Work in a copy of the Intermediate Example project, at its top: copy
`example_projects/intermediate/` from the download to a folder of your own, copy the
`sqlglot_composer` folder into it, as a Project holds it, and open a notebook there. This page
makes the same copy in its first step, from the download the Toolbox came in, into the folder
it runs in, which Python's path holds already, as Jupyter's does for a notebook's own folder:

>>> import shutil
>>> from pathlib import Path
>>> import sqlglot_composer
>>> download = Path(sqlglot_composer.__file__).parents[1]  # -> Path
>>> _ = shutil.copytree(download / "example_projects" / "intermediate", ".", dirs_exist_ok=True)

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> from warehouse import execute, query
>>> from references import ops
>>> from references.ops__job_events import ends_a_run  # -> Condition
>>> job_events = ops.job_events  # -> Table

### Write the change in a Building block

Keep the function in a Building block, a file of the Project's building_blocks/ folder, where
its line stays put and any notebook can import it. `project.new_block` makes the file, from
the Project's building_block Template, and registers it:

>>> project.new_block("run_speed")
Wrote building_blocks/run_speed.py, from admin/templates/building_block.py:
fill in its <...> and TODO lines.

Then write your function over the Template's code:

The file `building_blocks/run_speed.py`, after you write your function in it:

    \"\"\"run_speed - how each run's minutes compare with its job's usual run.

    Why: mart.run_speed saves these numbers, worked out in pandas, which does a median per
    group in one line.
    \"\"\"

    import pandas as pd


    def add_minutes_over_median(runs: pd.DataFrame) -> pd.DataFrame:
        \"\"\"runs, with minutes_over_median: the minutes each run took over its job's median
        run, the job's usual one.\"\"\"
        median = runs.groupby("job_id")["minutes"].transform("median")
        return runs.assign(minutes_over_median=runs["minutes"] - median)

>>> from building_blocks.run_speed import add_minutes_over_median

### Pull the rows with a Statement

A run's minutes are on the event that ends it, which ops.job_events' Alias `ends_a_run` picks.
The runs that ended on the Example database's last two days, with the columns the change reads.
`run` gives back a DataFrame:

>>> ended = statement(  # -> Statement
...     SELECT(job_events.event_id, job_events.job_id, job_events.minutes, job_events.dt),
...     FROM(job_events),
...     WHERE(between(job_events.dt, "2026-09-23", "2026-09-24"), ends_a_run),
... )
>>> runs = run(ended, query=query)  # -> DataFrame
>>> runs
   event_id  job_id  minutes          dt
0        52       1       12  2026-09-23
1        54       2       18  2026-09-23
2        56       1       10  2026-09-24

### Change them in pandas

Your function takes the DataFrame and gives back another, as any pandas code does:

>>> changed = add_minutes_over_median(runs)  # -> DataFrame
>>> changed
   event_id  job_id  minutes          dt  minutes_over_median
0        52       1       12  2026-09-23                  1.0
1        54       2       18  2026-09-23                  0.0
2        56       1       10  2026-09-24                 -1.0

Job 1's run on 2026-09-23 took a minute longer than its usual run.

### Make the table it saves to, and its notebook

The table the rows go to is a Saved table like any other, here mart.run_speed, made with
`project.new_table`, as [Save a table](#save_a_table) shows:

>>> project.new_table("mart.run_speed")
Made tables/mart__run_speed/: mart__run_speed.ipynb and lineage/, from
admin/templates/saved_table.py.
Wrote references/mart__run_speed.py: fill in its <...> and TODO lines.

The file `references/mart__run_speed.py`, after you fill it in:

    \"\"\"mart.run_speed - one row per run that ended: its minutes over its job's usual run.\"\"\"
    from sqlglot_composer import Table

    run_speed = Table(
        "mart.run_speed",
        columns={
            "event_id": "bigint",
            "job_id": "bigint",
            "minutes": "int",
            "minutes_over_median": "double",
            "dt": "string",
        },
        partitioned_by=["dt"],
        key=["event_id"],
        location="/data/your_team/mart.db/run_speed",
    )

Its notebook's logic cell says what the change reads and writes: rows() is the Statement
that pulls the rows, and write() gives the change, declared with `python_step`. The cell
after it pulls the rows, changes them and saves them, with your API's own write call, since
the Toolbox has no call that saves a DataFrame:

The file `tables/mart__run_speed/mart__run_speed.ipynb`, after you fill it in:

    # %% [markdown]
    # # mart.run_speed
    #
    # Each run that ended on the days READS picks, with the minutes it took over its job's
    # usual run, the median. The change is made in pandas, by add_minutes_over_median in
    # `building_blocks/run_speed.py`, and the rows are saved by your own call, in cell 3.
    #
    # The code cells: 1 the Project and your query; 2 the logic, which starts `# logic`; 3
    # pull, change and save the rows; 4 its lineage.

    # %%
    # 1. The Project and your query
    import pathlib
    import sys
    sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

    from sqlglot_composer import export_lineage, run
    from warehouse import query

    # %%
    # logic
    # 2. The logic: imports, the rows it reads, and functions only
    from sqlglot_composer import (
        FROM, SELECT, WHERE, PythonStep, Statement, create_table, equals, python_step, statement,
    )
    from building_blocks.run_speed import add_minutes_over_median
    from references.mart__run_speed import run_speed  # this table's own Table reference
    from references.ops__job_events import ends_a_run, job_events

    # The rows write() reads.
    READS = equals(job_events.dt, "2026-09-24")


    def create() -> Statement:
        \"\"\"Step 1: create mart.run_speed from its Table reference, if it isn't there yet.\"\"\"
        return create_table(run_speed, may_exist=True)


    def rows() -> Statement:
        \"\"\"The rows the change reads: each event READS picks that ends a run.\"\"\"
        return statement(
            SELECT(job_events.event_id, job_events.job_id, job_events.minutes, job_events.dt),
            FROM(job_events),
            WHERE(READS, ends_a_run),
        )


    def write() -> PythonStep:
        \"\"\"Step 2: the change, declared: what it reads, and the table it writes. Cell 3 makes
        it.\"\"\"
        return python_step(
            add_minutes_over_median,
            reads=[job_events.event_id, job_events.job_id, job_events.minutes, job_events.dt],
            writes=run_speed,
        )

    # %%
    # 3. Pull the rows, change them in pandas, and save them with your own call
    import my_api  # your team's API, as warehouse.py uses it

    changed = add_minutes_over_median(run(rows(), query=query))
    my_api.write_table(changed, "mart.run_speed", partition_by=["dt"])

    # %%
    # 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
    export_lineage(rows(), write())

### Declare the step

`python_step` takes your function itself, not what it gave back, the columns it read, each
through its Table reference (a Table reference stands for every one of its columns), and the
table it wrote. It gives back a `PythonStep`, and sends nothing. `project.load` runs the
notebook's logic cell, as `project.run_tables` does, so its write() is here too:

>>> speed = project.load("mart.run_speed")
>>> speed_step = speed.write()  # -> PythonStep
>>> speed_step
<Python step: building_blocks/run_speed.py:add_minutes_over_median, line 10; writes mart.run_speed>

It read where the function lives from the function itself: its file, from the Project's
folder, its name, and the line its `def` is on. `show_hive` prints what it is, as comment lines,
since it has no Hive:

>>> text = show_hive(speed_step)
-- Python step: changed in Python by building_blocks/run_speed.py:add_minutes_over_median,
-- line 10. It reads ops.job_events.event_id, ops.job_events.job_id, ops.job_events.minutes
-- and ops.job_events.dt, and writes mart.run_speed. Nothing is sent for it: your own call
-- saves its rows.

### A table that reads it is written after it

mart.slow_runs keeps the runs that took more than 5 minutes over their job's usual run, read
from mart.run_speed:

>>> project.new_table("mart.slow_runs")
Made tables/mart__slow_runs/: mart__slow_runs.ipynb and lineage/, from
admin/templates/saved_table.py.
Wrote references/mart__slow_runs.py: fill in its <...> and TODO lines.
Wrote references/mart.py: from references import mart gives mart.budget_overruns, mart.job_day_costs, mart.job_day_facts, mart.job_events_checks, mart.job_notes, mart.run_speed and mart.team_days.
Restart the kernel of a notebook that imported references, to see a table added since.

The file `references/mart__slow_runs.py`, after you fill it in:

    \"\"\"mart.slow_runs - one row per run that took over 5 minutes more than its job's usual run.\"\"\"
    from sqlglot_composer import Table

    slow_runs = Table(
        "mart.slow_runs",
        columns={"event_id": "bigint", "job_id": "bigint", "minutes_over_median": "double",
                 "dt": "string"},
        partitioned_by=["dt"],
        key=["event_id"],
        location="/data/your_team/mart.db/slow_runs",
    )

The file `tables/mart__slow_runs/mart__slow_runs.ipynb`, after you fill it in:

    # %% [markdown]
    # # mart.slow_runs
    #
    # Each run that took more than 5 minutes over its job's usual run, from mart.run_speed.
    #
    # The code cells: 1 the Project and your query; 2 the logic, which starts `# logic`; 3
    # try it; 4 its lineage.

    # %%
    # 1. The Project and your query
    import pathlib
    import sys
    sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

    from sqlglot_composer import export_lineage, show_hive
    from warehouse import query

    # %%
    # logic
    # 2. The logic: imports, the rows it reads, and functions only
    from sqlglot_composer import (
        FROM, INSERT_OVERWRITE, SELECT, WHERE, Statement, create_table, equals, more_than,
        statement,
    )
    from references.mart__run_speed import run_speed
    from references.mart__slow_runs import slow_runs  # this table's own Table reference

    # The rows write() reads.
    READS = equals(run_speed.dt, "2026-09-24")


    def create() -> Statement:
        \"\"\"Step 1: create mart.slow_runs from its Table reference, if it isn't there yet.\"\"\"
        return create_table(slow_runs, may_exist=True)


    def write() -> Statement:
        \"\"\"Step 2: save the runs READS picks that took over 5 minutes more than usual.\"\"\"
        return statement(
            INSERT_OVERWRITE(slow_runs),
            SELECT(run_speed.event_id, run_speed.job_id, run_speed.minutes_over_median,
                   run_speed.dt),
            FROM(run_speed),
            WHERE(READS, more_than(run_speed.minutes_over_median, 5)),
        )

    # %%
    # 3. Try it: the Hive of each step
    show_hive([create(), write()])

    # %%
    # 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
    export_lineage(write())

`project.run_tables` writes each table before the tables that read it. mart.slow_runs reads
what the Python step wrote, so it comes after it; with no execute, it prints each one in
order and sends nothing:

>>> project.run_tables(tables=["mart.slow_runs", "mart.run_speed"])
-- 1 of 2: mart.run_speed
-- Python step: changed in Python by building_blocks/run_speed.py:add_minutes_over_median,
-- line 10. It reads ops.job_events.event_id, ops.job_events.job_id, ops.job_events.minutes
-- and ops.job_events.dt, and writes mart.run_speed. Nothing is sent for it: your own call
-- saves its rows.
-- 2 of 2: mart.slow_runs
-- The Session setting "dynamic_partitions": this write fills dt from its rows.
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
INSERT OVERWRITE TABLE mart.slow_runs PARTITION(dt)
SELECT
  run_speed.event_id,
  run_speed.job_id,
  run_speed.minutes_over_median,
  run_speed.dt
FROM mart.run_speed AS run_speed
WHERE
  run_speed.dt = '2026-09-24' AND run_speed.minutes_over_median > 5;
Printed 2 writes in order, and sent nothing. Pass execute= to run them.

With your execute, it passes over the Python step, since it sends nothing for one, and says
so: run mart.run_speed's own notebook first, whose cell 3 saves its rows, so that
mart.slow_runs reads what it holds.

>>> project.run_tables(tables=["mart.slow_runs", "mart.run_speed"], query=query,
...                    execute=execute)
execute: SET hive.exec.dynamic.partition=true
execute: SET hive.exec.dynamic.partition.mode=nonstrict
1 of 2: mart.run_speed  passed over: a Python step, whose rows your own call saves
execute: INSERT OVERWRITE TABLE mart.slow_runs PARTITION(dt)
2 of 2: mart.slow_runs  worked
Wrote 1 table, in order.
Passed over 1 Python step, of mart.run_speed: run each one's notebook, whose own call saves its rows.

### Export the Lineage, the step drawn as one box

Pass the step to `export_lineage` with the Statements around it: the one that pulls its rows,
and the write that reads what it saved:

>>> slow = project.load("mart.slow_runs")
>>> html_file, markdown_file = export_lineage(speed.rows(), speed_step, slow.write(),
...                                           to="lineage/run_speed.html")

The chart draws the step as one box, "Python step", naming the function and its line, with
an arrow in from each column it read and out to each column of mart.run_speed. The Toolbox
can't see inside it, so it can't tell which column made which: the columns of mart.slow_runs
go back as far as the step, and the step's own section says what it read and where its
function lives.

## Check it worked

The step's section names the function and where it lives, and the write of mart.slow_runs
reads the table the step wrote:

>>> text = markdown_file.read_text(encoding="utf-8")
>>> "Changed in Python by `building_blocks/run_speed.py:add_minutes_over_median`, line 10." in text
True
>>> "It reads the Saved table mart.run_speed, written by" in text
True

## Common mistakes

### Running the step

A Python step only declares a change; the rows are yours to save. `run` refuses it:

>>> run(speed_step, execute=execute)
Traceback (most recent call last):
...
TypeError:
  What happened:  run was given a Python step, which sends nothing.
...

Save the rows with your own call, and pass the step to `export_lineage`.

### Passing what the function gave back

`add_minutes_over_median(runs)` is the changed DataFrame, not the function that changed it:

>>> python_step(add_minutes_over_median(runs), reads=[job_events.minutes],
...             writes=ops.job_events)
Traceback (most recent call last):
...
TypeError:
  What happened:  python_step was given a DataFrame, where the function that made the change goes.
...

Pass the function's name alone, with no brackets after it.

### A lambda

A lambda has no name, so the Lineage couldn't say where to find it:

>>> python_step(lambda rows: rows, reads=[job_events.minutes], writes=ops.job_events)
Traceback (most recent call last):
...
ValueError:
  What happened:  python_step was given a lambda.
...

Write the change with `def` and a name, in a Building block that `project.new_block` made.

## Next

- Compare the Lineage before and after you change the function:
  [Review and test a change](#review_and_test_a_change).
- More of what pandas does with the rows `run` gives back: [Look across rows](#look_across_rows).
- The gallery's [`python_step`](examples.html#python_step) and
  [`export_lineage`](examples.html#export_lineage) entries.
"""
