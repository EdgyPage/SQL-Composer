"""Declare a change made in Python

For: Intermediate

## Goal

Change some rows in pandas, in a function of your own, save them to a table with your own
call, and declare the change to the Toolbox with `python_step`. A Python step is such a change,
made outside any Statement, the query the Toolbox builds, and declared with the columns it read
and the table it wrote. Declared, it lets the Lineage of your tables, the record of which
columns feed each result, show where the change lives, rather than stopping at the gap, and
`project.run_tables` write the tables that read it after it.

## When you'd use it

- If a step is easier in pandas than in a Statement, make it a Python step. Here it is how many
  minutes longer each run took than its job's usual run, the median, which pandas works out in
  one line.
- If you need the Toolbox to move the rows, use a Statement instead: for a Python step you pull
  the rows with a Statement, change them with your function, and save them with your work's own
  call. `python_step` only tells the Toolbox which columns the change read, which table it
  wrote, and which function made it, so whoever reads the Lineage can open that function and
  see what it does.
- If you have not saved a table, made a Building block or exported Lineage yet, do
  [Save a table](#save_a_table), [Share Building blocks](#share_building_blocks) and
  [Follow lineage](#follow_lineage) first.

## Steps

### 1. Start from the Intermediate Example project

Goal: a Project, your folder of scripts at work, to make the change in. Work in a copy of the
Intermediate Example project, at its top: copy `example_projects/intermediate/` from the
download to a folder of your own, copy the `sqlglot_composer` folder into it, as a Project holds
it, and open a notebook there. This page makes the same copy in its first step, from the
download the Toolbox came in, into the folder it runs in, which Python's path holds already, as
Jupyter's does for a notebook's own folder:

>>> import shutil
>>> from pathlib import Path
>>> import sqlglot_composer
>>> download = Path(sqlglot_composer.__file__).parents[1]  # -> Path
>>> _ = shutil.copytree(download / "example_projects" / "intermediate", ".", dirs_exist_ok=True)

Done when the folder you work in holds the Project's admin/, references/ and tables/ folders.
Then step 2.

### 2. Import the names the steps use

Goal: the Toolbox, your query and execute, and ops.job_events with its Alias `ends_a_run`, a
name its Table reference gives a condition on it:

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> from warehouse import connect, query, execute
>>> connect(example_database)
>>> from references import ops
>>> from references.ops__job_events import ends_a_run  # -> Condition
>>> job_events = ops.job_events  # -> Table

Done when `job_events` and `ends_a_run` are set. Then step 3.

### 3. Make a Building block for the change

Goal: a file for your function. Keep the function in a Building block, a file of the Project's
building_blocks/ folder, where its line stays put and any notebook can import it.
`project.new_block` makes the file, from the Project's building_block Template, and registers
it:

>>> project.new_block("run_speed")
Wrote building_blocks/run_speed.py, from admin/templates/building_block.py:
fill in its <...> and TODO lines.

Done when building_blocks/run_speed.py is written. Then step 4.

### 4. Write the change in it

Goal: your function, importable. Write your function over the Template's code:

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

Done when `add_minutes_over_median` imports. Then step 5.

### 5. Pull the rows with a Statement

Goal: the rows the change reads, as a DataFrame. A run's minutes are on the event that ends
it, which ops.job_events' Alias `ends_a_run` picks. The runs that ended on the Example
database's last two days, with the columns the change reads. `run_query` gives back a
DataFrame:

>>> ended = statement(  # -> Statement
...     SELECT(job_events.event_id, job_events.job_id, job_events.minutes, job_events.dt),
...     FROM(job_events),
...     WHERE(between(job_events.dt, "2026-09-23", "2026-09-24"), ends_a_run),
... )
>>> runs = run_query(ended, query)  # -> DataFrame
>>> runs
   event_id  job_id  minutes          dt
0        52       1       12  2026-09-23
1        54       2       18  2026-09-23
2        56       1       10  2026-09-24

Done when `runs` holds events 52, 54 and 56. Then step 6.

### 6. Change them in pandas

Goal: the changed rows. Your function takes the DataFrame and gives back another, as any pandas
code does:

>>> changed = add_minutes_over_median(runs)  # -> DataFrame
>>> changed
   event_id  job_id  minutes          dt  minutes_over_median
0        52       1       12  2026-09-23                  1.0
1        54       2       18  2026-09-23                  0.0
2        56       1       10  2026-09-24                 -1.0

Job 1's run on 2026-09-23 took a minute longer than its usual run.

Done when `changed` has the column minutes_over_median. Then step 7.

### 7. Make the table it saves to

Goal: a Saved table, a real table your own code writes, for the changed rows, with its Table
reference, the file that describes it. The table the rows go to is a Saved table like any
other, here mart.run_speed, made with `project.new_table`, as [Save a table](#save_a_table)
shows:

>>> project.new_table("mart.run_speed")
Made tables/mart__run_speed/: mart__run_speed.ipynb and lineage/, from
admin/templates/saved_table.py.
Wrote references/mart__run_speed.py: project.reference_from_logic writes it.

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

Done when references/mart__run_speed.py names the table's five columns. Then step 8.

### 8. Fill in its Table notebook

Goal: the notebook that pulls, changes and saves the rows. A Table notebook is the notebook in a
Table folder whose cells create and write its Saved table. Its logic cell says what the change
reads and writes: rows() is the Statement that pulls the rows, and write() gives the change,
declared with `python_step`. The cell after it pulls the rows, changes them and saves them,
with your API's own write call, since the Toolbox has no call that saves a DataFrame:

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

    from sqlglot_composer import export_lineage, run_query
    from warehouse import connect, query

    # Your connection to the warehouse. Each notebook runs on its own, so each connects here, at
    # its top, before it calls query or execute: write yours in the line below and delete its #,
    # such as connect(your_library.connect(...)). A connection kept in a file outside the Project,
    # such as team_connection.py, is imported by these lines, written in that line's place:
    #     sys.path.append("C:/work/connections")  # the folder team_connection.py is in
    #     from team_connection import conn
    #     connect(conn)
    # connect(your_connection)

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

    changed = add_minutes_over_median(run_query(rows(), query))
    my_api.write_table(changed, "mart.run_speed", partition_by=["dt"])

    # %%
    # 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
    export_lineage(rows(), write())

Done when the notebook's logic cell has rows() and write(). Then step 9.

### 9. Declare the step

Goal: the change, declared as a `PythonStep`. `python_step` takes your function itself, not
what it gave back, the columns it read, each through its Table reference (a Table reference
stands for every one of its columns), and the table it wrote. It gives back a `PythonStep`, and
sends nothing. `project.load` runs the notebook's logic cell, as `project.run_tables` does, so
its write() is here too:

>>> speed = project.load("mart.run_speed")  # -> the notebook's functions
>>> speed_step = speed.write()  # -> PythonStep
>>> speed_step
<Python step: building_blocks/run_speed.py:add_minutes_over_median, line 10; writes
    mart.run_speed>

It read where the function lives from the function itself: its file, from the Project's
folder, its name, and the line its `def` is on. `show_hive` prints what it is, as comment lines,
since it has no Hive:

>>> text = show_hive(speed_step)
-- Python step: changed in Python by building_blocks/run_speed.py:add_minutes_over_median,
-- line 10. It reads ops.job_events.event_id, ops.job_events.job_id, ops.job_events.minutes
-- and ops.job_events.dt, and writes mart.run_speed. Nothing is sent for it: your own call
-- saves its rows.

Done when `show_hive` names add_minutes_over_median and line 10. Then step 10.

### 10. Make a table that reads it

Goal: a second Saved table, written from what the Python step saved. mart.slow_runs keeps the
runs that took more than 5 minutes over their job's usual run, read from mart.run_speed:

>>> project.new_table("mart.slow_runs")
Made tables/mart__slow_runs/: mart__slow_runs.ipynb and lineage/, from
admin/templates/saved_table.py.
Wrote references/mart__slow_runs.py: project.reference_from_logic writes it.
Wrote references/mart.py: from references import mart gives mart.budget_overruns,
    mart.job_day_costs, mart.job_day_facts, mart.job_events_checks, mart.job_notes,
    mart.run_speed, mart.team_days and mart.team_failures.
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
    from warehouse import connect, query

    # Your connection to the warehouse. Each notebook runs on its own, so each connects here, at
    # its top, before it calls query or execute: write yours in the line below and delete its #,
    # such as connect(your_library.connect(...)). A connection kept in a file outside the Project,
    # such as team_connection.py, is imported by these lines, written in that line's place:
    #     sys.path.append("C:/work/connections")  # the folder team_connection.py is in
    #     from team_connection import conn
    #     connect(conn)
    # connect(your_connection)

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

Done when mart.slow_runs' Table reference and notebook are filled in. Then step 11.

### 11. Write the tables in order

Goal: each table written after the tables it reads. `project.run_tables` writes each table
before the tables that read it. mart.slow_runs reads what the Python step wrote, so it comes
after it; with no execute, it prints each one in order and sends nothing:

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

>>> project.run_tables(tables=["mart.slow_runs", "mart.run_speed"], execute=execute)
execute: SET hive.exec.dynamic.partition=true
execute: SET hive.exec.dynamic.partition.mode=nonstrict
1 of 2: mart.run_speed  passed over: a Python step, whose rows your own call saves
execute: INSERT OVERWRITE TABLE mart.slow_runs PARTITION(dt)
2 of 2: mart.slow_runs  worked
Wrote 1 table, in order.
Passed over 1 Python step, of mart.run_speed: run each one's notebook, whose own call saves its
    rows.

Done when it says it passed over the Python step of mart.run_speed and wrote mart.slow_runs.
Then step 12.

### 12. Export the Lineage, the step drawn as one box

Goal: Lineage that shows where the change lives. Pass the step to `export_lineage` with the
Statements around it: the one that pulls its rows, and the write that reads what it saved:

>>> slow = project.load("mart.slow_runs")  # -> the notebook's functions
>>> html_file, markdown_file = export_lineage(
...     speed.rows(), speed_step, slow.write(),  # -> tuple[Path, Path]
...     to="lineage/run_speed.html")

The chart draws the step as one box, "Python step", naming the function and its line, with
an arrow in from each column it read and out to each column of mart.run_speed. The Toolbox
can't see inside it, so it can't tell which column made which: the columns of mart.slow_runs
go back as far as the step, and the step's own section says what it read and where its
function lives.

Done when export_lineage has written lineage/run_speed.html and its .md beside it. Then check
it worked, below.

## Check it worked

The step's section names the function and where it lives, and the write of mart.slow_runs
reads the table the step wrote:

>>> text = markdown_file.read_text(encoding="utf-8")
>>> "Changed in Python by `building_blocks/run_speed.py:add_minutes_over_median`, line 10." in text
True
>>> "It reads the Saved table mart.run_speed, written by" in text
True

Before you go on, check that:

- the Lineage's step section names building_blocks/run_speed.py, add_minutes_over_median and
  line 10;
- the Lineage says mart.slow_runs reads the Saved table mart.run_speed;
- `project.run_tables` lists mart.run_speed before mart.slow_runs.

## Common mistakes

### Running the step

A Python step only declares a change; the rows are yours to save. `run_execute` refuses it:

>>> run_execute(speed_step, execute)
Traceback (most recent call last):
...
TypeError:
  What happened:  run_execute was given a Python step, which sends nothing.
...

Save the rows with your own call, and pass the step to `export_lineage`.

### Passing what the function gave back

`add_minutes_over_median(runs)` is the changed DataFrame, not the function that changed it:

>>> python_step(add_minutes_over_median(runs), reads=[job_events.minutes],
...             writes=ops.job_events)
Traceback (most recent call last):
...
TypeError:
  What happened:  python_step was given a DataFrame, where the function that made the change
                  goes.
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
- More of what pandas does with the rows `run_query` gives back:
  [Look across rows](#look_across_rows).
- The gallery's [`python_step`](examples.html#python_step) and
  [`export_lineage`](examples.html#export_lineage) entries.
"""  # noqa: E501 - the files it writes, byte for byte, and a step with no brackets to break in
