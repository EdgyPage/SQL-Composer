"""Follow lineage

For: Getting started

## Goal

See where each column of a Statement's result comes from: the table columns that feed it, the
conditions that decide which rows count towards it, and the Hive that ran. `export_lineage`
writes this Lineage as two files, an HTML page to explore in your browser and a Markdown file
to read anywhere. You export one Statement's, then a Saved table's from its Table notebook,
into its Table folder's lineage/, then a table that reads another Saved table, drawn together
with it, all the way back to the tables they start from; `project.run_tables` writes them in
that same order. Last, a change made in pandas is declared with `python_step`, so the Lineage
doesn't stop at it.

## When you'd use it

- Before you hand someone a number, so you can answer "where does this come from?" by
  pointing at the files.
- When a number looks wrong: the Markdown file lists every condition that decides which rows
  count towards it, from every step, in one place.
- Whenever a Saved table's logic changes: each export is kept, beside the ones before, to
  compare.

## Steps

### Where the last how-to left the Project

[Save a table](#save_a_table) left the Project with its Table references, its Building block
and one Saved table. This how-to reads two of the Table references and the
Building block, so the steps make those again, shortened; mart.alerts_per_severity isn't read
here, so it is left out:

>>> import os
>>> from pathlib import Path
>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/ and warehouse.py.
Next: write your two functions, query and execute, in warehouse.py.
>>> from warehouse import query, execute
>>> project.add_references(["ops.jobs", "ops.job_runs"], query=query)
Wrote references/ops__jobs.py and references/ops__job_runs.py: fill in their TODO lines.
Wrote references/ops.py: from references import ops gives ops.job_runs and ops.jobs.
Restart the kernel of a notebook that imported references, to see a table added since.
>>> project.new_block("runs_per_job")
Wrote building_blocks/runs_per_job.py, from admin/templates/building_block.py:
fill in its <...> and TODO lines.

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
    )

    minutes = job_runs.duration_mins
    failed = equals(job_runs.status, "FAILED")

The file `references/ops__jobs.py`, after you fill it in:

    \"\"\"ops.jobs - one row per job: its name, the team that owns it and its region.\"\"\"
    from sqlglot_composer import Table

    jobs = Table(
        "ops.jobs",
        columns={"job_id": "bigint", "job_name": "string", "team": "string", "region": "string"},
        key=["job_id"],
        does_not_add_up=[],
    )

The file `building_blocks/runs_per_job.py`, after you fill it in:

    \"\"\"runs_per_job - each job's runs, failed runs and minutes for each dt it reads.\"\"\"

    from sqlglot_composer import (
        AS, FROM, GROUP_BY, SELECT, WHERE, Condition, Table, count_rows, derived, statement,
        sum_of,
    )
    from references.ops__job_runs import failed, job_runs, minutes  # failed, minutes: Aliases


    def runs_per_job(reads: Condition) -> Table:
        \"\"\"One row per job for each dt of the rows `reads` picks: its runs, failed runs and
        minutes.\"\"\"
        return derived(
            "runs_per_job",
            statement(
                SELECT(
                    job_runs.job_id,
                    job_runs.dt,
                    AS(count_rows(), "runs"),
                    AS(count_rows(where=failed), "failed_runs"),
                    AS(sum_of(minutes), "minutes"),
                ),
                FROM(job_runs),
                WHERE(reads),
                GROUP_BY(job_runs.job_id, job_runs.dt),
            ),
        )

The steps run in a notebook in the Project's folder, which Jupyter puts on Python's path:

>>> from references import ops

### Export one Statement's Lineage

The Statement here counts each team's runs, and their failed runs, over two days:

>>> team_runs = statement(  # -> Statement
...     SELECT(
...         ops.jobs.team,
...         AS(count_rows(), "runs"),
...         AS(count_rows(where=equals(ops.job_runs.status, "FAILED")), "failed_runs"),
...     ),
...     FROM(ops.job_runs),
...     JOIN(ops.jobs, ON=equals(ops.jobs.job_id, ops.job_runs.job_id)),
...     WHERE(between(ops.job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(ops.jobs.team),
... )
>>> run(team_runs, query=query)  # -> DataFrame
      team  runs  failed_runs
0     data     4            0
1  finance     5            2

`export_lineage` takes the Statement itself, not its Hive or its result. It writes the two
files and gives back their paths, the HTML page first. Nothing is sent to the warehouse: the
Lineage is worked out from the Statement alone.

Where the files go, and their names, take one of two forms. Each name starts with `<time>`,
the time it ran, such as `20260925-090000` for 09:00:00 on 2026-09-25, so each export gets a
name of its own and the ones before stay as they were. The HTML page and the Markdown file
share the name, ending `.html` and `.md`:

- a Statement exported outside a Table notebook, as here, goes in a folder named lineage
  beside the notebook you run it from, at the Project's top for a notebook there, named
  `<time>_<commit>_lineage_<notebook>_<variable>.md`: `<commit>` is the git commit of your
  scripts, here pinned to `1a2b3c4` (`"nogit"` outside a git repository), `<notebook>` the
  notebook's name (`"notebook"` where the steps don't run in a saved one), and `<variable>` the
  name of the variable that holds the Statement, here `team_runs`. So put a Statement in a
  variable with a meaningful name before you export it;
- a write of a Saved table goes in its Table folder's lineage/, wherever you run it, named
  `<time>-<database>__<table>.md`, such as `20260925-090000-mart__daily_job_runs.md`, as the
  next step shows.

`to=`, such as `to="lineage/team_runs.html"`, names the files instead, replacing the last.

>>> html_file, markdown_file = export_lineage(team_runs)  # -> tuple[Path, Path]
>>> markdown_file.name  # -> str
'20260925-090000_1a2b3c4_lineage_notebook_team_runs.md'
>>> markdown_file.parent.name  # -> str
'lineage'

Read the Markdown file from the top. Graph is a chart in Mermaid, a text format for charts that
JupyterLab and GitHub draw: each table read is a group holding the columns the Statement uses,
a solid arrow carries a value, and a dotted one carries a column into a condition. Then the
Statement's own section, `team_runs`:

- Calculated columns: each column worked out rather than copied, here `"runs"` and
  `"failed_runs"`, with a small tree down to the table columns it reads (`"failed_runs"` reads
  `ops.job_runs.status`), its Rows that count, every condition that decides which rows count
  (here the two days in WHERE, and the match in JOIN's `ON=`; when a number looks wrong, look
  here first), and what one row stands for, from GROUP_BY;
- Copied columns: `"team"`, from `ops.jobs.team`;
- Keys: which columns tell the rows apart, here `"team"`;
- Hive as submitted: the Hive `run` sends.

The HTML page draws the same Lineage as boxes and arrows: click a box to light up every column
it comes from and every condition that decides its rows. It needs no internet.

### Export a Saved table's Lineage, from its Table notebook

mart.daily_job_runs saves each job's runs, failed runs and minutes per day, from the Building
block. Make its Table folder, and fill in its notebook and its Table reference, as [Save a
table](#save_a_table) does; here they are filled in, shortened from the Starter Example
project's:

>>> project.new_table("mart.daily_job_runs")
Made tables/mart__daily_job_runs/: mart__daily_job_runs.ipynb and lineage/, from
admin/templates/saved_table.py.
Wrote references/mart__daily_job_runs.py: fill in its <...> and TODO lines.

The file `references/mart__daily_job_runs.py`, after you fill it in:

    \"\"\"mart.daily_job_runs - one row per job and day: runs, failed runs and minutes.\"\"\"

    from sqlglot_composer import Table

    daily_job_runs = Table(
        "mart.daily_job_runs",
        columns={
            "job_id": "bigint",
            "runs": "bigint",
            "failed_runs": "bigint",
            "minutes": "bigint",
            "dt": "string",
        },
        partitioned_by=["dt"],
        key=["job_id", "dt"],
        location="/data/your_team/mart.db/daily_job_runs",
    )

The file `tables/mart__daily_job_runs/mart__daily_job_runs.ipynb`, after you fill it in:

    # %% [markdown]
    # # mart.daily_job_runs
    #
    # Each job's runs, failed runs and minutes per day. Where the saved_table Template counts
    # the rows READS picks, its rows come from the Building block runs_per_job, given READS.

    # %%
    # 1. The Project and your query
    import pathlib
    import sys
    sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

    from sqlglot_composer import export_lineage, project, run, show_hive
    from warehouse import query

    # %%
    # logic
    # 2. The logic: imports, the rows it reads, and functions only
    from sqlglot_composer import (
        FROM, INSERT_OVERWRITE, SELECT, Clause, Statement, create_table, equals, statement,
    )
    from building_blocks.runs_per_job import runs_per_job
    from references.mart__daily_job_runs import daily_job_runs
    from references.ops__job_runs import job_runs

    # The rows write() reads: change it to write others.
    READS = equals(job_runs.dt, "2026-09-24")


    def create() -> Statement:
        \"\"\"Step 1: create mart.daily_job_runs from its Table reference, if it isn't there.\"\"\"
        return create_table(daily_job_runs, may_exist=True)


    def rows() -> list[Clause]:
        \"\"\"The clauses preview and write share: each job's numbers, from the Building block.\"\"\"
        per_job = runs_per_job(READS)
        return [
            SELECT(per_job.job_id, per_job.runs, per_job.failed_runs, per_job.minutes,
                   per_job.dt),
            FROM(per_job),
        ]


    def preview() -> Statement:
        \"\"\"Step 2: the rows write() would save, as a SELECT to run and check first.\"\"\"
        return statement(*rows())


    def write() -> Statement:
        \"\"\"Step 3: save the rows, replacing the Partitions they fill.\"\"\"
        return statement(INSERT_OVERWRITE(daily_job_runs), *rows())

    # %%
    # 3. Try it: the Hive of each step, then the rows
    show_hive([create(), write()])
    run(preview(), query=query)

    # %%
    # 4. Lineage: a new pair in lineage/, named by the time and this table
    export_lineage(write())

    # %%
    # 5. The Reference sheet: this table's rows, from references/mart__daily_job_runs.py
    project.refresh_reference_sheet("mart.daily_job_runs")

Cell 4 exports the table's Lineage. Here, `project.load` gives the notebook's logic, as its
cell 2 does when it runs: an object with one attribute per function of the logic cell, such
as `daily.write`. The write goes in a variable with a meaningful name first:

>>> daily = project.load("mart.daily_job_runs")  # -> the notebook's functions
>>> write_daily_job_runs = daily.write()  # -> Statement
>>> html_file, markdown_file = export_lineage(write_daily_job_runs)  # -> tuple[Path, Path]
>>> markdown_file.relative_to(Path.cwd()).as_posix()  # -> str
'tables/mart__daily_job_runs/lineage/20260925-090000-mart__daily_job_runs.md'

The write fills a table with a Table folder, so the pair goes in that folder's lineage/, named
by the time and the table alone, the second form above. Each export adds a pair, so lineage/
keeps every one before: the table's history, oldest first, to compare when its logic changes. Its Graph
draws the Building block as a group of its own, named `"runs_per_job"` as the block names it:
`"failed_runs"` is counted there, from `ops.job_runs.status`, and copied into the table.

### Draw a table that reads another Saved table

mart.team_day adds up each team's day from what mart.daily_job_runs saved. It reads the Saved
table through its Table reference, like any other table. Its notebook below is shortened from
the Starter Example project's, whose cell 3 also runs a function of its logic,
team_runs_from_job_runs, each team's day worked out from ops.job_runs itself, so that it runs
on the Example database:

>>> project.new_table("mart.team_day")
Made tables/mart__team_day/: mart__team_day.ipynb and lineage/, from
admin/templates/saved_table.py.
Wrote references/mart__team_day.py: fill in its <...> and TODO lines.
Wrote references/mart.py: from references import mart gives mart.daily_job_runs.
Restart the kernel of a notebook that imported references, to see a table added since.

The file `references/mart__team_day.py`, after you fill it in:

    \"\"\"mart.team_day - one row per team and day: runs, failed runs and minutes.\"\"\"

    from sqlglot_composer import Table

    team_day = Table(
        "mart.team_day",
        columns={
            "team": "string",
            "runs": "bigint",
            "failed_runs": "bigint",
            "minutes": "bigint",
            "dt": "string",
        },
        partitioned_by=["dt"],
        key=["team", "dt"],
        location="/data/your_team/mart.db/team_day",
    )

The file `tables/mart__team_day/mart__team_day.ipynb`, after you fill it in:

    # %% [markdown]
    # # mart.team_day
    #
    # Each team's runs, failed runs and minutes per day, added up from mart.daily_job_runs.

    # %%
    # 1. The Project and your query
    import pathlib
    import sys
    sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

    from sqlglot_composer import export_lineage, project, run, show_hive
    from warehouse import query

    # %%
    # logic
    # 2. The logic: imports, the rows it reads, and functions only
    from sqlglot_composer import (
        AS, FROM, GROUP_BY, INSERT_OVERWRITE, JOIN, SELECT, WHERE, Clause, Statement,
        create_table, equals, statement, sum_of,
    )
    from references.mart__daily_job_runs import daily_job_runs
    from references.mart__team_day import team_day
    from references.ops__jobs import jobs

    # The rows write() reads: change it to write others.
    READS = equals(daily_job_runs.dt, "2026-09-24")


    def create() -> Statement:
        \"\"\"Step 1: create mart.team_day from its Table reference, if it isn't there yet.\"\"\"
        return create_table(team_day, may_exist=True)


    def rows() -> list[Clause]:
        \"\"\"The clauses preview and write share: each team's numbers, from daily_job_runs.\"\"\"
        return [
            SELECT(
                jobs.team,
                AS(sum_of(daily_job_runs.runs), "runs"),
                AS(sum_of(daily_job_runs.failed_runs), "failed_runs"),
                AS(sum_of(daily_job_runs.minutes), "minutes"),
                daily_job_runs.dt,
            ),
            FROM(daily_job_runs),
            JOIN(jobs, ON=equals(jobs.job_id, daily_job_runs.job_id)),
            WHERE(READS),
            GROUP_BY(jobs.team, daily_job_runs.dt),
        ]


    def preview() -> Statement:
        \"\"\"Step 2: the rows write() would save, as a SELECT to run and check first.\"\"\"
        return statement(*rows())


    def write() -> Statement:
        \"\"\"Step 3: save the rows, once mart.daily_job_runs has written them.\"\"\"
        return statement(INSERT_OVERWRITE(team_day), *rows())

    # %%
    # 3. Try it: the Hive of each step. Its preview reads mart.daily_job_runs, which only
    # your warehouse holds, so it runs at work: run(preview(), query=query)
    show_hive([create(), write()])

    # %%
    # 4. Lineage: both tables together. project.load gives the other notebook's logic, so its
    # write() can be drawn here too, each in a variable named for it.
    daily = project.load("mart.daily_job_runs")
    write_daily_job_runs = daily.write()
    write_team_day = write()
    export_lineage(write_daily_job_runs, write_team_day)

    # %%
    # 5. The Reference sheet: this table's rows, from references/mart__team_day.py
    project.refresh_reference_sheet("mart.team_day")

Its Lineage alone would stop at mart.daily_job_runs, with nothing behind it. So cell 4 loads
the logic of the table it reads, and passes both writes. One write goes in its own Table
folder's lineage/ wherever you run it, but with several writes the folder you run from decides
where they go: the lineage/ of the Table folder you run them from, when one of them fills its
table, or else beside your notebook. Jupyter runs a notebook in its own folder, so the steps
move there first, as opening the notebook would, then do what cell 4 does:

>>> os.chdir("tables/mart__team_day")
>>> team = project.load("mart.team_day")  # -> the notebook's functions
>>> write_team_day = team.write()  # -> Statement
>>> html_file, markdown_file = export_lineage(  # -> tuple[Path, Path]
...     write_daily_job_runs, write_team_day)
>>> markdown_file.name  # -> str
'20260925-090000-mart__team_day.md'

The files go in this Table folder's lineage/, named for its own table. The order you pass them in doesn't matter: `export_lineage` puts each write before the ones
that read the Saved table it fills. The Markdown file has a section for each write. The
second's first line says it reads mart.daily_job_runs, written by write_daily_job_runs above,
so the tree of the team's `"failed_runs"` goes on through the Saved table, and the Building
block, back to `ops.job_runs.status`: the file answers "what counts as a failed run here?" in
one place.

### Write them in that order

`project.run_tables` writes every table in the order the Lineage draws them: a table before any
table that reads it, found from each write's Hive. With your query and execute, from
warehouse.py, which here hold the Example database's, it sends each in turn, and the Example
database's execute prints the first line of each. It takes query= as well as execute=, since
a write() may give an Admin statement or an Unchecked statement, and one that reads rows goes
to your query:

>>> os.chdir("../..")
>>> project.run_tables(query=query, execute=execute)
execute: SET hive.exec.dynamic.partition=true
execute: SET hive.exec.dynamic.partition.mode=nonstrict
execute: WITH runs_per_job AS (
1 of 2: mart.daily_job_runs  worked
execute: INSERT OVERWRITE TABLE mart.team_day PARTITION(dt)
2 of 2: mart.team_day        worked
Wrote 2 tables, in order.

mart.team_day goes after mart.daily_job_runs, so it reads the rows that were just written.
mart.daily_job_runs's write starts `WITH runs_per_job AS (`, not INSERT: its rows come from
the Building block, a Derived table, which the Hive writes at its top, ahead of the INSERT
OVERWRITE that reads it.

### Declare a change made in pandas, in a Table notebook

Some steps are easier in pandas than in a Statement, such as how many minutes longer each run
took than its job's usual run, the median. The Toolbox never moves the rows: you pull them with
a Statement, change them with your own function, and save them with your work's own call.
`python_step` declares the change, so the Lineage shows where it lives rather than stopping at
the gap. In a Table notebook, write() gives the Python step, and the notebook's cell 3 pulls,
changes and saves. Make the Table folder as usual, then write over the Template's logic:

>>> project.new_table("mart.run_speed")
Made tables/mart__run_speed/: mart__run_speed.ipynb and lineage/, from
admin/templates/saved_table.py.
Wrote references/mart__run_speed.py: fill in its <...> and TODO lines.
Wrote references/mart.py: from references import mart gives mart.daily_job_runs and mart.team_day.
Restart the kernel of a notebook that imported references, to see a table added since.

The file `references/mart__run_speed.py`, after you fill it in:

    \"\"\"mart.run_speed - one row per run: its minutes, and how many over its job's usual run.\"\"\"

    from sqlglot_composer import Table

    run_speed = Table(
        "mart.run_speed",
        columns={
            "run_id": "bigint",
            "job_id": "bigint",
            "duration_mins": "int",
            "minutes_over_median": "double",
            "dt": "string",
        },
        partitioned_by=["dt"],
        key=["run_id", "dt"],
        location="/data/your_team/mart.db/run_speed",
    )

The file `tables/mart__run_speed/mart__run_speed.ipynb`, after you fill it in:

    # %% [markdown]
    # # mart.run_speed
    #
    # Each run of a day, with how many minutes longer it took than its job's usual run. pandas
    # works that out, so cell 3 pulls the runs, changes them and saves them with your own call;
    # write() gives the Python step that declares the change.

    # %%
    # 1. The Project and your query
    import pathlib
    import sys
    sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

    from sqlglot_composer import export_lineage, project, run, show_hive
    from warehouse import query

    # %%
    # logic
    # 2. The logic: imports, the rows it reads, and functions only
    import pandas as pd

    from sqlglot_composer import (
        FROM, SELECT, WHERE, PythonStep, Statement, create_table, equals, python_step,
        statement,
    )
    from references.mart__run_speed import run_speed
    from references.ops__job_runs import job_runs

    # The rows the change reads: change it to write others.
    READS = equals(job_runs.dt, "2026-09-24")


    def create() -> Statement:
        \"\"\"Step 1: create mart.run_speed from its Table reference, if it isn't there yet.\"\"\"
        return create_table(run_speed, may_exist=True)


    def preview() -> Statement:
        \"\"\"Step 2: the rows the change reads, pulled with a Statement.\"\"\"
        return statement(
            SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt),
            FROM(job_runs),
            WHERE(READS),
        )


    def add_minutes_over_median(runs: pd.DataFrame) -> pd.DataFrame:
        \"\"\"The minutes each run took over its job's median run, its usual one.\"\"\"
        median = runs.groupby("job_id")["duration_mins"].transform("median")
        return runs.assign(minutes_over_median=runs["duration_mins"] - median)


    def write() -> PythonStep:
        \"\"\"Step 3: what writes mart.run_speed: the change above, which your own call saves.\"\"\"
        return python_step(
            add_minutes_over_median,
            reads=[job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt],
            writes=run_speed,
        )

    # %%
    # 3. Pull the rows, change them in pandas, and save them with your own call
    show_hive([create(), write()])
    runs = run(preview(), query=query)
    changed = add_minutes_over_median(runs)
    # at work, your own call saves them, once create() has made the table:
    # my_api.write_table(changed, "mart.run_speed", partition_by=["dt"])
    changed

    # %%
    # 4. Lineage: the Python step, drawn as one box
    export_lineage(write())

    # %%
    # 5. The Reference sheet: this table's rows, from references/mart__run_speed.py
    project.refresh_reference_sheet("mart.run_speed")

Its function lives in the logic cell, so any notebook that loads the logic can call it. Cell 3
pulls the rows and changes them:

>>> speed = project.load("mart.run_speed")  # -> the notebook's functions
>>> runs = run(speed.preview(), query=query)  # -> DataFrame
>>> changed = speed.add_minutes_over_median(runs)  # -> DataFrame
>>> changed
   run_id  job_id  duration_mins          dt  minutes_over_median
0     101       1             10  2026-09-24                -15.0
1     102       2             20  2026-09-24                  0.0
2     103       3             30  2026-09-24                  0.0
3     104       1             40  2026-09-24                 15.0

The Toolbox has no call that saves a DataFrame: you save it the way your work does, such as
your API's own write call, which cell 3 shows in a comment, since it reaches your warehouse.
`speed.write()` gives the Python step: your function itself, not what it gave back, the columns it
read, and the table it wrote. It sends nothing, and `show_hive` prints what it is:

>>> speed_step = speed.write()  # -> PythonStep
>>> text = show_hive(speed_step)  # -> str
-- Python step: changed in Python by
-- tables/mart__run_speed/mart__run_speed.ipynb:add_minutes_over_median, line 30 of its cell.
-- It reads ops.job_runs.run_id, ops.job_runs.job_id, ops.job_runs.duration_mins and
-- ops.job_runs.dt, and writes mart.run_speed. Nothing is sent for it: your own call saves
-- its rows.

Where the function lives is read from the function: a function in a Table notebook's logic
cell is named by its notebook, and its line is a line of that cell. Its Lineage draws the step
as one box, from the columns it read to each column of mart.run_speed: the Toolbox can't see
inside it, and its section says where to open the function.

`project.run_tables` puts the step in order with the other tables, by the tables it reads and
writes, and passes over it, since your own call saves its rows:

>>> project.run_tables(query=query, execute=execute)
execute: SET hive.exec.dynamic.partition=true
execute: SET hive.exec.dynamic.partition.mode=nonstrict
execute: WITH runs_per_job AS (
1 of 3: mart.daily_job_runs  worked
execute: INSERT OVERWRITE TABLE mart.team_day PARTITION(dt)
2 of 3: mart.team_day        worked
3 of 3: mart.run_speed       passed over: a Python step, whose rows your own call saves
Wrote 2 tables, in order.
Passed over 1 Python step, of mart.run_speed: run each one's notebook, whose own call saves its rows.

A table whose write() reads mart.run_speed is written after it, and reads what mart.run_speed
holds then: the rows your own call saved the last time its notebook ran. So run that notebook,
cell 3 and its save, before `project.run_tables`, on each day its rows should change.

## Check it worked

Each Table folder's lineage/ holds its pair, and mart.team_day's has a section for each write,
reaching back through the Saved table to `ops.job_runs`:

>>> sorted(path.name for path in Path("tables/mart__team_day/lineage").iterdir())
['20260925-090000-mart__team_day.html', '20260925-090000-mart__team_day.md']
>>> text = markdown_file.read_text(encoding="utf-8")  # -> str
>>> [line for line in text.splitlines() if line.startswith("## ")]
['## Graph', '## write_daily_job_runs', '## write_team_day']
>>> "written by write_daily_job_runs above" in text, "ops.job_runs.status" in text
(True, True)

## Common mistakes

### Exporting the reading table's write on its own

mart.team_day's write alone draws mart.daily_job_runs as a table like any other, with nothing
behind it:

>>> alone_html, alone_markdown = export_lineage(  # -> tuple[Path, Path]
...     write_team_day, to="lineage/team_alone.html")
>>> "ops.job_runs" in alone_markdown.read_text(encoding="utf-8")
False

Its trees stop at mart.daily_job_runs: nothing says how the job counts were made. Pass every
write the table reads from, as cell 4 does: `export_lineage` follows a Saved table only between
the Statements it is given.

### Passing the list of writes as one argument

`show_hive` takes a list, but `export_lineage` takes each Statement as its own argument, and
refuses a list:

>>> export_lineage([write_daily_job_runs, write_team_day])
Traceback (most recent call last):
...
TypeError:
  What happened:  export_lineage was given [...], which isn't a Statement that reads a table.
...

Name each write, as cell 4 does.

### Loading a table that has no Table folder

`project.load` runs the notebook in a table's Table folder. A table the Project only reads,
such as `ops.job_runs`, has none, and is refused:

>>> project.load("ops.job_runs")
Traceback (most recent call last):
...
FileNotFoundError:
  What happened:  project.load("ops.job_runs"): there is no tables/ops__job_runs/ops__job_runs.ipynb.
...

A table the Project only reads has no write to draw: its columns are where each tree starts.

## Next

- Find a column in the Reference sheet, check each Table reference against its table, and keep
  the Project tidy: [Keep the Project in order](#keep_the_project_in_order).
- Compare a table's Lineage before and after a change: [Review and test a
  change](#review_and_test_a_change).
- More on a change made in Python: [Declare a change made in
  Python](#declare_a_change_made_in_python).
- The gallery's [`export_lineage`](examples.html#export_lineage) and
  [`python_step`](examples.html#python_step) entries.
"""
