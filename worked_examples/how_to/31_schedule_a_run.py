"""Schedule a run

For: Intermediate

## Goal

Make a Scheduled run: a notebook in your Project that an outside scheduler, such as papermill or
your team's, runs top to bottom, writing the tables it needs in order and reading back what you
asked for. You name the Statements it is for, from your Table notebooks' logic; its Build cell
adds the writes of each table they read, all the way up, and prints their Hive, sending
nothing; its Run cell sends them. Each value the scheduler passes in is a Parameter, read by
its type hint before anything is built.

## When you'd use it

- If one job of your scheduler should write a few tables and read back one result, not run the
  whole Project, make a Scheduled run for it, as the steps below do.
- If you want the run's Hive to read before it is ever sent, build it, as step 5 does: nothing
  is sent until the Run cell.
- If a run failed partway, run it again with the `START_FROM` it printed, as step 7 says.
- If you want the run's lineage, or its Hive in a file to commit, export them by hand, as step
  8 does: a Scheduled run writes neither when it runs.

## Steps

### 1. Start from the Intermediate Example project

Goal: a Project with Saved tables for a run to write. Work in a copy of the Intermediate
Example project, at its top: copy `example_projects/intermediate/` from the download to a
folder of your own, copy the `sqlglot_composer` folder into it, as a Project holds it, and open
a notebook there. This page makes the same copy in its first step, then connects, as each
notebook does at its top, to the Example database, which stands in for your warehouse:

>>> import shutil
>>> from pathlib import Path
>>> import sqlglot_composer
>>> download = Path(sqlglot_composer.__file__).parents[1]  # -> Path
>>> _ = shutil.copytree(download / "example_projects" / "intermediate", ".", dirs_exist_ok=True)
>>> from sqlglot_composer import example_database, project, statement
>>> from warehouse import connect, execute, query
>>> connect(example_database)

Done when the folder you work in holds the Project's scheduled_runs/ folder. Then step 2.

### 2. See what a table's logic offers

Goal: the functions a run can call. A Saved table's Table notebook has a logic cell, the cell
that starts `# logic`, whose functions each give a Statement. `project.describe_logic` lists
them, each with what it takes and the first sentence of what it does, and runs nothing:

>>> print(project.describe_logic("mart.team_days"))
# mart.team_days: project.load("mart.team_days"), from the # logic cell of tables/mart__team_days/mart__team_days.ipynb
def create() -> Statement:
    \"\"\"Step 1: create mart.team_days from its Table reference, if it isn't there yet.\"\"\"
def rows(first_day: str, last_day: str) -> list[Clause]:
    \"\"\"The clauses every step below shares: each team's numbers per day of job_day_facts, the table in FROM.\"\"\"
def preview() -> Statement:
    \"\"\"Step 2: the rows write() would save, as a SELECT to run and check first.\"\"\"
def write_days(first_day: str, last_day: str) -> Statement:
    \"\"\"Every day from first_day to last_day, in one write.\"\"\"
def write() -> Statement:
    \"\"\"Step 3, every run, once the two tables it reads have written the same days: the last 3 days, ending on DAY, in one write.\"\"\"
def week_totals(first_day: str, last_day: str) -> Statement:
    \"\"\"Each team's events, runs, minutes and cost per week, from the days this table saved.\"\"\"
def team_day_from_job_events(day: str) -> Statement:
    \"\"\"Each team's events, runs and minutes for a day, from ops.job_events and ops.job_owners themselves, through the Building blocks mart.job_day_facts saves: so it runs on the Example database.\"\"\"

This run calls two of them: write(), which saves mart.team_days's last 3 days, ending on the
day its own logic cell names, and team_day_from_job_events(day), a SELECT of each team's
numbers for the day you give it. At work a run would read back the table it just wrote; here
the SELECT reads ops tables, since the Example database holds no mart table to read. Paste
the same list into a Copilot chat, after Copilot file 18, and Copilot fills in the run for you.

Done when you know the functions the run calls. Then step 3.

### 3. Make the run

Goal: the run's notebook. `project.new_scheduled_run` makes it from the scheduled_run
Template in admin/templates/, in a folder of its own under scheduled_runs/, and registers it:

>>> print(project.new_scheduled_run("team_day"))
Made scheduled_runs/team_day/: team_day.ipynb, from admin/templates/scheduled_run.py.
Fill in its <...>: its parameters, its connection and the Statements it runs.

In your Project, admin/scheduled_runs.ipynb makes the same call: name the run in its cell
`NEW_RUNS = ["team_day"]` and run that cell. Its `TABLES = ["mart.team_days"]` cell runs
step 2's `project.describe_logic` the same way.

Done when scheduled_runs/team_day/team_day.ipynb is there. Then step 4.

### 4. Fill in its cells

Goal: a run that builds. Open team_day.ipynb in Jupyter. Its cells run top to bottom:

- `# parameters`, tagged "parameters", papermill's tag: each value the scheduler passes in, a
  name, its type hint and its default. A scheduler passes text, so each is read by its hint:
  `datetime.date` from `"2026-09-24"`, `int`, `float`, `bool` from "true" or "false", and
  `str`, each alone, in `list[...]` (its items split at commas) or with `| None`. Keep
  `START_FROM`.
- the setup cell: the Project on Python's path, the Toolbox, and your connection in its
  `connect(...)` line.
- `# scheduled`: `statements()`, which gives the Statements the run is for, each by its name;
  a SELECT's rows come back by it.
- the Build cell, `project.build_run(statements, ...)`, and the Run cell,
  `built.run(query, execute)`.

Fill in a parameter, `READ_DAY`, the connection and the two Statements, by these rules:

- A parameter reaches only what `statements()` passes it to: here the SELECT. write() takes
  nothing, so it writes the days its own logic cell names, whatever READ_DAY is.
- team_day_from_job_events takes its day as text, `day: str`, so `str(READ_DAY)` gives it the
  date as '2026-09-23'.
- Each Statement's name is the key of the dict: a SELECT's rows come back by it, and a write's
  is only a label, since the build heads each write by its table.

Once every `<...>` is gone, you may cut its text cell down to what the run is for, as here:

The file `scheduled_runs/team_day/team_day.ipynb`, after you fill it in:

    # %% [markdown]
    # # Scheduled run: team_day
    #
    # Each day: mart.team_days written, with the tables it reads, then each team's numbers
    # for READ_DAY read back, as results["team_day"].

    # %%
    # parameters
    # The values a scheduler passes in, each a name, its type hint and its default. A scheduler
    # passes text, which the Build cell reads by the hint, and refuses a value it can't read. The
    # hints it reads: datetime.date, int, float, bool, str, each alone, in list[...] or with
    # | None, such as list[datetime.date] for "2026-11-01,2026-11-08".
    import datetime  # for a datetime.date hint

    START_FROM: str = ""  # a table or SELECT to start from, as a failed run prints it; "" sends all
    READ_DAY: datetime.date = datetime.date(2026, 9, 24)  # the day to read back, such as "2026-09-24"

    # %%
    # Setup: the Project on Python's path, the Toolbox and your connection
    import pathlib
    import sys
    sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

    from sqlglot_composer import Statement, project, statement
    from warehouse import connect, execute, query

    from sqlglot_composer import example_database
    connect(example_database)

    # %%
    # scheduled
    # The Statements this run sends, each by its name: a SELECT's rows come back in results by it.


    def statements() -> dict[str, Statement]:
        \"\"\"What this run sends, by name: the build adds the writes of each table they read.\"\"\"
        team_days = project.load("mart.team_days")
        return {
            "team_days": team_days.write(),
            "team_day": team_days.team_day_from_job_events(str(READ_DAY)),
        }

    # %%
    # Build: the Statements, in order, and their Hive, printed; nothing sent
    built = project.build_run(statements, run_values={}, leave_out=[])

    # %%
    # Run: each one sent, in the build's order
    results = built.run(query, execute)

At work, the setup cell's connection is yours, in place of the Example database. Done when no
code cell holds a `<...>`. Then step 5.

### 5. Build it

Goal: the run's Hive, in order, to read before anything is sent. Run the cells down to the
Build cell. Jupyter runs a notebook in its own folder, so the lines below move there first, as
opening the notebook would, then run its cells, the setup cell's connection already made
above. A scheduler passes `READ_DAY` as text, which papermill puts in a cell after the parameters
cell, as the line `READ_DAY = "2026-09-23"` here stands in for:

>>> import datetime
>>> import os
>>> os.chdir("scheduled_runs/team_day")
>>> START_FROM: str = ""
>>> READ_DAY: datetime.date = datetime.date(2026, 9, 24)
>>> READ_DAY = "2026-09-23"  # as a scheduler passes it: text
>>> def statements():
...     team_days = project.load("mart.team_days")
...     return {
...         "team_days": team_days.write(),
...         "team_day": team_days.team_day_from_job_events(str(READ_DAY)),
...     }
>>> built = project.build_run(statements, run_values={}, leave_out=[])
Parameters, as this run uses them:
  START_FROM = ""
  READ_DAY = datetime.date(2026, 9, 23), read as datetime.date from "2026-09-23"
-- 1 of 4: team_day
WITH events_per_job AS (
  SELECT
    job_events.job_id,
    job_events.dt,
    COUNT(*) AS events,
    COUNT(CASE WHEN job_events.event_type = 'start' THEN 1 END) AS runs,
    COALESCE(
      SUM(
        CASE WHEN job_events.event_type IN ('finish', 'fail') THEN job_events.minutes END
      ),
      0
    ) AS minutes
  FROM ops.job_events AS job_events
  WHERE
    job_events.dt BETWEEN '2026-09-23' AND '2026-09-23'
  GROUP BY
    job_events.job_id,
    job_events.dt
)
SELECT
  job_owners.team,
  SUM(events_per_job.events) AS events,
  SUM(events_per_job.runs) AS runs,
  SUM(events_per_job.minutes) AS minutes
FROM events_per_job
LEFT JOIN ops.job_owners AS job_owners
  ON job_owners.job_id = events_per_job.job_id
  AND job_owners.dt = events_per_job.dt
  AND job_owners.dt BETWEEN '2026-09-23' AND '2026-09-23'
GROUP BY
  job_owners.team;
-- 2 of 4: mart.job_day_costs (read by mart.team_days)
-- Session settings: dynamic_partitions, sent one line at a time
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
WITH costs_per_job AS (
  SELECT
    region_costs.job_id,
    SUM(region_costs.cost_cents) AS cost_cents,
    CONCAT(
      SUBSTRING(region_costs.dt, 1, 4),
      '-',
      SUBSTRING(region_costs.dt, 5, 2),
      '-',
      SUBSTRING(region_costs.dt, 7, 2)
    ) AS dt
  FROM ops.region_costs AS region_costs
  WHERE
    region_costs.dt BETWEEN '20260922' AND '20260924'
  GROUP BY
    region_costs.job_id,
    CONCAT(
      SUBSTRING(region_costs.dt, 1, 4),
      '-',
      SUBSTRING(region_costs.dt, 5, 2),
      '-',
      SUBSTRING(region_costs.dt, 7, 2)
    )
)
INSERT OVERWRITE TABLE mart.job_day_costs PARTITION(dt)
SELECT
  costs_per_job.job_id,
  costs_per_job.cost_cents,
  costs_per_job.dt
FROM costs_per_job;
-- 3 of 4: mart.job_day_facts (read by mart.team_days)
WITH events_per_job AS (
  SELECT
    job_events.job_id,
    job_events.dt,
    COUNT(*) AS events,
    COUNT(CASE WHEN job_events.event_type = 'start' THEN 1 END) AS runs,
    COALESCE(
      SUM(
        CASE WHEN job_events.event_type IN ('finish', 'fail') THEN job_events.minutes END
      ),
      0
    ) AS minutes
  FROM ops.job_events AS job_events
  WHERE
    job_events.dt BETWEEN '2026-09-22' AND '2026-09-24'
  GROUP BY
    job_events.job_id,
    job_events.dt
)
INSERT OVERWRITE TABLE mart.job_day_facts PARTITION(dt)
SELECT
  events_per_job.job_id,
  job_owners.team,
  events_per_job.events,
  events_per_job.runs,
  events_per_job.minutes,
  events_per_job.dt
FROM events_per_job
LEFT JOIN ops.job_owners AS job_owners
  ON job_owners.job_id = events_per_job.job_id
  AND job_owners.dt = events_per_job.dt
  AND job_owners.dt BETWEEN '2026-09-22' AND '2026-09-24';
-- 4 of 4: mart.team_days
INSERT OVERWRITE TABLE mart.team_days PARTITION(dt)
SELECT
  job_day_facts.team,
  SUM(job_day_facts.events) AS events,
  SUM(job_day_facts.runs) AS runs,
  SUM(job_day_facts.minutes) AS minutes,
  SUM(job_day_costs.cost_cents) AS cost_cents,
  job_day_facts.dt
FROM mart.job_day_facts AS job_day_facts
LEFT JOIN mart.job_day_costs AS job_day_costs
  ON job_day_costs.job_id = job_day_facts.job_id
  AND job_day_costs.dt = job_day_facts.dt
  AND job_day_costs.dt BETWEEN '2026-09-22' AND '2026-09-24'
WHERE
  job_day_facts.dt BETWEEN '2026-09-22' AND '2026-09-24'
GROUP BY
  job_day_facts.dt,
  job_day_facts.team;
Built 4 Statements in order, and sent nothing: results = built.run(query, execute) sends them.

It printed each parameter as used, `READ_DAY` read as a date from the text it was given, then
each Statement under a heading, in the order the run sends them. You named two; the build
added the writes of mart.job_day_costs and mart.job_day_facts, the two Saved tables
mart.team_days's write reads, before it, each as its own Table notebook's write() writes it,
on its own days: READ_DAY reaches none of them. Each table is written after the tables it
reads, and the SELECT, which reads only ops tables, can go first.

Done when it prints each Statement's Hive and says it sent nothing. Then step 6.

### 6. Run it

Goal: the Statements sent and the SELECT's rows back. The Run cell sends each in the build's
order, each write through your `execute` and each SELECT through your `query`, printing a line
as each works. The Session setting "dynamic_partitions" goes once, before the first write
that fills its Partitions from its rows, as the build printed it under that write's heading,
and holds for every write after it; the Example database prints the first line of each change
it is given, `execute: ...`, and writes nothing:

>>> results = built.run(query, execute)
1 of 4: team_day            worked: 2 rows, in results["team_day"]
execute: SET hive.exec.dynamic.partition=true
execute: SET hive.exec.dynamic.partition.mode=nonstrict
execute: WITH costs_per_job AS (
2 of 4: mart.job_day_costs  worked
execute: WITH events_per_job AS (
3 of 4: mart.job_day_facts  worked
execute: INSERT OVERWRITE TABLE mart.team_days PARTITION(dt)
4 of 4: mart.team_days      worked
Sent 4 Statements in order. results holds the rows of team_day, by name, as results["team_day"].
>>> results["team_day"]
      team  events  runs  minutes
0     data       2     1       12
1  finance       2     1       18

Done when it ends with no error, and `results["team_day"]` holds each team's numbers. Then
step 7.

### 7. Schedule it

Goal: the scheduler runs the notebook. Have your scheduler run team_day.ipynb top to bottom,
from its own folder, passing each parameter as text. With papermill, which runs a notebook and
saves a copy of it with each cell's output, that is a command such as
"papermill team_day.ipynb runs/team_day_2026-09-23.ipynb -p READ_DAY 2026-09-23", typed in
a terminal opened in scheduled_runs/team_day/. Its "-p READ_DAY 2026-09-23" passes READ_DAY
as text, which the Build cell reads as a date, as in step 5. papermill finds the parameters
cell by its tag: in JupyterLab, the cell's tags are in the right sidebar's Property
Inspector; the Template's cell has it already. The saved copy is the run's record: what the
build printed, each parameter as used first, and each line the run printed. Nothing else is
written as it runs.

If one fails, the run stops there, prints the tables it wrote before it and a line such as
`START_FROM = "mart.team_days"`, and raises its error, so the scheduler sees the notebook fail.
Run it again with that value, `-p START_FROM mart.team_days`, and the build passes over each
Statement before that table's first write. A SELECT it passes over isn't sent, so its rows
aren't in `results`: here team_day, sent first, is passed over, and only a plain run gives
`results["team_day"]`. A plain run again, `START_FROM` left `""`, is safe too: here, each
write is an INSERT_OVERWRITE, as each `INSERT OVERWRITE TABLE` line the build printed in step
5 shows, which replaces the Partitions it fills. A write made with INSERT_INTO, printed as
`INSERT INTO TABLE`, adds its rows each time it is sent, so a run holding one runs again only
with the `START_FROM` it printed.

Done when your scheduler runs it with the parameters it needs. Then step 8.

### 8. Export its Hive and lineage by hand

Goal: the run's Hive in a file to read and commit, and its lineage. Neither is written as the
run runs, since that would be work for nothing each time: admin/scheduled_runs.ipynb holds
the cells that write them, by hand, from the Project's top. `project.export_run_hive` builds
the run as its Build cell does, with its parameters' defaults, and writes its Hive into
team_day.hql beside its notebook, to read, never to edit or to send:

>>> os.chdir("../..")
>>> print(project.export_run_hive("team_day"))
Wrote scheduled_runs/team_day/team_day.hql: the Hive of 4 Statements, in the order the run sends them, built as its Build cell builds them, with the defaults of its # parameters cell, sending nothing. It is to read, never to edit: the notebook builds its Hive again each time it runs.

`project.export_run_lineage("team_day")` writes its lineage into the run's lineage/ folder the same
way, and `project.export_project_lineage()` draws every Saved table of the Project, with the
Scheduled runs that write each.

Done when scheduled_runs/team_day/ holds team_day.hql. Then check it worked, below.

## Check it worked

Before you go on, check that:

- scheduled_runs/team_day/ holds team_day.ipynb, and no code cell holds a `<...>`;
- its Build cell prints each parameter as used, then each Statement's Hive, and sends nothing;
- its Run cell ends with no error, and `results` holds each SELECT's rows by its name;
- `project.check()` says every Scheduled run is registered.

## Common mistakes

### A parameter with no type hint

The Build cell reads each parameter by its hint, so one written `READ_DAY = "2026-09-24"`,
with no hint, is refused before anything is built, naming it. Give it a hint,
`READ_DAY: datetime.date = ...`.

### A value that can't be read

A scheduler that passes `READ_DAY` as `"23/09/2026"` is refused, naming `READ_DAY`, its hint
and the value: a `datetime.date` is read from a day written as 2026-09-23 alone, year, month
and day. Nothing is built or sent.

### Expecting a parameter to move the tables the build adds

A parameter reaches only what `statements()` passes it to. Each write the build adds is its
Table notebook's write(), on the days its logic gives it, so here mart.job_day_facts writes
its own last 3 days whatever READ_DAY is. To move a write's days with the run, pass the
parameter in yourself, as an argument, such as `team_days.write_days(str(READ_DAY), str(READ_DAY))`; or, where
its days are a Run value, give that Run value the parameter by its function's name,
`run_values={"period_end": READ_DAY}`, which reaches the write the build adds too.

### A table another run writes

The build adds each table the Statements read, so two runs may write the same table. It is
shown, never refused: `project.export_project_lineage()` marks a table more than one run
writes. If another run writes it, leave it out here, `leave_out=["mart.job_day_facts"]`, and
the build adds none of what only it reads.

### Composing a quick Statement

A Statement composed in the run's own `# scheduled` cell, with `statement(...)`, is built even
where a Guard would refuse it elsewhere, when Hive runs it as written, such as a WHERE on a
LEFT_JOIN's table: it only warns, and the build lists each one it let through, with its line.
Why: a run's own cell is for quick Statements you mean as written, and a Table notebook's
logic is where a Statement others build on is checked in full. So a Statement from a Table
notebook's logic, through `project.load`, keeps every Guard, and a Load limit, which stops a
read of too much, still refuses anywhere.

### Editing the .hql file

team_day.hql is what the run built when you exported it: the run builds its Hive again each
time it runs, and never reads the file. Edit the notebook, save it, and export again.

## Next

- [Declare a change made in Python](#declare_a_change_made_in_python): a Python step's table,
  which a Scheduled run writes too, given `rows=`.
- [Follow lineage](#follow_lineage): a Statement's Lineage, column by column.
"""  # noqa: E501 - the lines describe_logic and export_run_hive print, shown whole
