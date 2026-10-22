"""Declare a change made in Python

For: Intermediate

## Goal

Change some rows in pandas, in a function of your own, save them to a table with your own
call, and declare the change to the Toolbox with `python_step`, so the Lineage of your tables
shows where the change lives, rather than stopping at the gap.

## When you'd use it

When a step is easier in pandas than in a Statement. Here it is how many minutes longer each
run took than its job's usual run, the median, which pandas works out in one line. The
Toolbox never moves the rows: you pull them with a Statement, change them with your function,
and save them with your work's own call. `python_step` only tells the Toolbox which columns the
change read, which table it wrote, and which function made it, so whoever reads the Lineage
can open that function and see what it does.

## Steps

### Start a Project and write the change in a Building block

Keep the function in a file of the Project's building_blocks/ folder, where its line stays put
and any notebook can import it. This page writes the file for you; in your own Project, which
is started already, leave out `project.start()` and make the file in your editor.

>>> import sys
>>> from pathlib import Path
>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/ and warehouse.py. Next: write your query and execute in warehouse.py.
>>> run_speed_py = '''# How each run's minutes compare with its job's usual run.
...
... import pandas as pd
...
...
... def add_minutes_over_median(runs: pd.DataFrame) -> pd.DataFrame:
...     # The minutes each run took over its job's median run, the job's usual one.
...     median = runs.groupby("job_id")["duration_mins"].transform("median")
...     return runs.assign(minutes_over_median=runs["duration_mins"] - median)
... '''
>>> _ = Path("building_blocks/run_speed.py").write_text(run_speed_py, encoding="utf-8")

A notebook imports it once the Project's folder is on Python's path, as cell 1 of a Table
notebook puts it. This page works in the Project's own folder, so the folder is this one:

>>> sys.path.insert(0, str(Path.cwd()))  # the Project folder
>>> from building_blocks.run_speed import add_minutes_over_median

### Pull the rows with a Statement

The runs that worked on the Example database's last two days, with the columns the change
reads. `run` gives back a DataFrame:

>>> job_runs = example_database.job_runs
>>> worked = statement(
...     SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"),
...           equals(job_runs.status, "SUCCESS")),
... )
>>> runs = run(worked, query=example_database.query)
>>> runs
   run_id  job_id  duration_mins          dt
0      95       1             12  2026-09-23
1      96       2             18  2026-09-23
2     101       1             10  2026-09-24
3     103       3             30  2026-09-24
4     104       1             40  2026-09-24

### Change them in pandas

Your function takes the DataFrame and gives back another, as any pandas code does:

>>> changed = add_minutes_over_median(runs)
>>> changed
   run_id  job_id  duration_mins          dt  minutes_over_median
0      95       1             12  2026-09-23                  0.0
1      96       2             18  2026-09-23                  0.0
2     101       1             10  2026-09-24                 -2.0
3     103       3             30  2026-09-24                  0.0
4     104       1             40  2026-09-24                 28.0

Run 104 took 28 minutes longer than job 1's usual run.

### Save them with your own call

The table the rows go to has a Table reference like any other, here mart.run_speed. In your
Project it is references/mart__run_speed.py, as [Describe a table by
hand](#describe_a_table_by_hand) writes one; this page makes it in place:

>>> run_speed = Table(
...     "mart.run_speed",
...     columns={"run_id": "bigint", "job_id": "bigint", "duration_mins": "int",
...              "minutes_over_median": "double", "dt": "string"},
...     partitioned_by=["dt"],
...     location="/data/your_team/mart.db/run_speed",
... )

The Toolbox has no call that saves a DataFrame: you save it the way your work does, such as
your API's own write call. It is shown here, not run, since it reaches your warehouse:

    my_api.write_table(changed, "mart.run_speed", partition_by=["dt"])

### Declare the step

`python_step` takes your function itself, not what it gave back, the columns it read, each
through its Table reference (a Table reference stands for every one of its columns), and the
table it wrote. It gives back a `PythonStep`, and sends nothing:

>>> speed_step = python_step(
...     add_minutes_over_median,
...     reads=[job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt],
...     writes=run_speed,
... )
>>> speed_step
<Python step: building_blocks/run_speed.py:add_minutes_over_median, line 6; writes mart.run_speed>

It read where the function lives from the function itself: its file, from the Project's
folder, its name, and the line its `def` is on. `show_hive` prints what it is, as comment lines,
since it has no Hive:

>>> text = show_hive(speed_step)
-- Python step: changed in Python by building_blocks/run_speed.py:add_minutes_over_median,
-- line 6. It reads ops.job_runs.run_id, ops.job_runs.job_id, ops.job_runs.duration_mins and
-- ops.job_runs.dt, and writes mart.run_speed. Nothing is sent for it: your own call saves
-- its rows.

### Export the Lineage, the step drawn as one box

Pass the step to `export_lineage` with the Statements around it, here one that reads
mart.run_speed: the runs that took more than 5 minutes over their job's usual run. The step
comes first, since it writes the table the Statement reads:

>>> slow_runs = statement(
...     SELECT(run_speed.run_id, run_speed.minutes_over_median),
...     FROM(run_speed),
...     WHERE(equals(run_speed.dt, "2026-09-24"), more_than(run_speed.minutes_over_median, 5)),
... )
>>> html_file, markdown_file = export_lineage(slow_runs, speed_step, to="run_speed.html")

The chart draws the step as one box, "Python step", naming the function and its line, with
an arrow in from each column it read and out to each column of mart.run_speed. The Toolbox
can't see inside it, so it can't tell which column made which: the copied columns of
slow_runs go back as far as the step, and the step's own section says what it read and where
its function lives.

In a Project, a Table notebook's write() may give the step beside its Statements, so
`project.run_tables` puts it in order with the tables it reads and writes. It sends nothing for
it, and says it passed it over: run that table's own notebook, whose call saves its rows.

## Check it worked

The step's section names the function and where it lives, and slow_runs reads the table the
step wrote:

>>> text = markdown_file.read_text(encoding="utf-8")
>>> "Changed in Python by `building_blocks/run_speed.py:add_minutes_over_median`, line 6." in text
True
>>> "It reads the Saved table mart.run_speed, written by speed_step above." in text
True

## Common mistakes

### Running the step

A Python step only declares a change; the rows are yours to save. `run` refuses it:

>>> run(speed_step, execute=example_database.execute)
Traceback (most recent call last):
...
TypeError:
  What happened:  run was given a Python step, which sends nothing.
...

Save the rows with your own call, and pass the step to `export_lineage`.

### Passing what the function gave back

`add_minutes_over_median(runs)` is the changed DataFrame, not the function that changed it:

>>> python_step(add_minutes_over_median(runs), reads=[job_runs.duration_mins],
...             writes=run_speed)
Traceback (most recent call last):
...
TypeError:
  What happened:  python_step was given a DataFrame, where the function that made the change goes.
...

Pass the function's name alone, with no brackets after it.

### A lambda

A lambda has no name, so the Lineage couldn't say where to find it:

>>> python_step(lambda rows: rows, reads=[job_runs.duration_mins], writes=run_speed)
Traceback (most recent call last):
...
ValueError:
  What happened:  python_step was given a lambda.
...

Write the change with `def` and a name, in a file of building_blocks/.

## Next

- Compare the Lineage before and after you change the function:
  [Review a change with Lineage](#review_a_change_with_lineage).
- More on finishing a job in pandas: [Look across rows, then finish in
  pandas](#finish_in_pandas).
- The gallery's [`python_step`](examples.html#python_step) and
  [`export_lineage`](examples.html#export_lineage) entries.
"""
