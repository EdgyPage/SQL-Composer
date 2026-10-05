"""A pipeline of Saved tables

For: Intermediate

## Goal

Build a pipeline in steps, each written from the step before: each job's day from the raw
events, saved in one Saved table, then each team's day from that, saved in another, then a
weekly rollup that adds up the team's saved days whenever you read it. You give each Saved
table its Table reference and its write, put the day's writes in one list that runs every
writer before the Statements that read its table, and export one Lineage for the whole chain.

## When you'd use it

When one number goes through several steps, and several notebooks or dashboards read the steps
in between. Each Saved table is worked out once a day and saved, so its readers read a few saved
rows rather than every raw row again, and each step can be checked on its own.

## Steps

### Import the Toolbox

The pipeline starts from two tables of the Example database: `ops.job_events`, what each job's
runs did each day, and `ops.job_owners`, each job's team on each day.

>>> from sqlglot_composer import *
>>> job_events = example_database.job_events
>>> job_owners = example_database.job_owners

### Describe each Saved table

Each Saved table has a Table reference written by hand, since it doesn't exist until you create
it, as in [Save a table](#save_a_table). mart.job_day holds each job's runs started and finished
per day; mart.team_day adds them up per team, as of each day. At work each goes in a file of
its own under table_references/.

>>> job_day = Table(
...     "mart.job_day",
...     columns={"job_id": "bigint", "starts": "bigint", "finishes": "bigint", "dt": "string"},
...     date_partition="dt",
...     key=["job_id", "dt"],
... )
>>> team_day = Table(
...     "mart.team_day",
...     columns={"team": "string", "starts": "bigint", "finishes": "bigint", "dt": "string"},
...     date_partition="dt",
...     key=["team", "dt"],
... )

Create each once. `show_hive` prints both, ready to paste:

>>> text = show_hive(create_table(job_day, may_exist=True),
...                  create_table(team_day, may_exist=True))
-- 1 of 2
CREATE TABLE IF NOT EXISTS mart.job_day (
  job_id BIGINT,
  starts BIGINT,
  finishes BIGINT
)
PARTITIONED BY (
  dt STRING
)
STORED AS ORC;
<BLANKLINE>
-- 2 of 2
CREATE TABLE IF NOT EXISTS mart.team_day (
  team STRING,
  starts BIGINT,
  finishes BIGINT
)
PARTITIONED BY (
  dt STRING
)
STORED AS ORC;

### Write each Saved table's day

Each write is a function of the day it writes. mart.job_day is written from the raw events:

>>> def write_job_day(day):
...     return statement(
...         INSERT_OVERWRITE(job_day),
...         SELECT(job_events.job_id,
...                AS(count_rows(where=equals(job_events.event_type, "start")), "starts"),
...                AS(count_rows(where=equals(job_events.event_type, "finish")), "finishes")),
...         FROM(job_events),
...         WHERE(equals(job_events.dt, day)),
...         GROUP_BY(job_events.dt, job_events.job_id),
...     )

mart.team_day is written from mart.job_day, read through its Table reference, `job_day`, like
any other table, with each job's team taken from that day's copy of the owners, as [Look things
up as of a day](#look_things_up_as_of_a_day) does. Adding up the jobs' counts into the team's is
safe: a sum of counts is still the right count.

>>> def write_team_day(day):
...     return statement(
...         INSERT_OVERWRITE(team_day),
...         SELECT(job_owners.team,
...                AS(sum_of(job_day.starts), "starts"),
...                AS(sum_of(job_day.finishes), "finishes")),
...         FROM(job_day),
...         JOIN(job_owners, ON=all_of(equals(job_owners.job_id, job_day.job_id),
...                                    equals(job_owners.dt, job_day.dt))),
...         WHERE(equals(job_day.dt, day), equals(job_owners.dt, day)),
...         GROUP_BY(job_day.dt, job_owners.team),
...     )

### Read the weekly rollup from mart.team_day

A write fills one day of its Saved table, the one day its `FROM` table reads, so the tables you
save hold days. The weekly rollup isn't saved: it is a Statement that adds up mart.team_day's
saved days into weeks whenever you read it, which is quick, since each day holds a row per team.
Read whole weeks, from a Monday to a Sunday; here the week holding 2026-09-24, the day the
pipeline below writes:

>>> def weekly_rollup(first_day, last_day):
...     return statement(
...         SELECT(AS(week_start(team_day.dt), "week"), team_day.team,
...                AS(sum_of(team_day.starts), "starts"),
...                AS(sum_of(team_day.finishes), "finishes")),
...         FROM(team_day),
...         WHERE(between(team_day.dt, first_day, last_day)),
...         GROUP_BY("week", team_day.team),
...     )
>>> weekly = weekly_rollup("2026-09-21", "2026-09-27")

### Put the day's writes in order

A Saved table must be written after the tables it is written from, or its write reads a day they
haven't written yet, and nothing would stop it. So one function lists the day's writes in that
order, each writer before its readers, and it is the only place that order is kept, as in [Run
a daily pipeline](#run_a_daily_pipeline):

>>> def pipeline(day):
...     return [write_job_day(day), write_team_day(day)]
>>> job_day_step, team_day_step = pipeline("2026-09-24")
>>> text = show_hive(job_day_step, team_day_step)
-- 1 of 2: job_day_step
INSERT OVERWRITE TABLE mart.job_day PARTITION(dt = '2026-09-24')
SELECT
  job_events.job_id,
  COUNT(CASE WHEN job_events.event_type = 'start' THEN 1 END) AS starts,
  COUNT(CASE WHEN job_events.event_type = 'finish' THEN 1 END) AS finishes
FROM ops.job_events AS job_events
WHERE
  job_events.dt = '2026-09-24'
GROUP BY
  job_events.dt,
  job_events.job_id;
<BLANKLINE>
-- 2 of 2: team_day_step
INSERT OVERWRITE TABLE mart.team_day PARTITION(dt = '2026-09-24')
SELECT
  job_owners.team,
  SUM(job_day.starts) AS starts,
  SUM(job_day.finishes) AS finishes
FROM mart.job_day AS job_day
JOIN ops.job_owners AS job_owners
  ON job_owners.job_id = job_day.job_id AND job_owners.dt = job_day.dt
WHERE
  job_day.dt = '2026-09-24' AND job_owners.dt = '2026-09-24'
GROUP BY
  job_day.dt,
  job_owners.team;

That printout is a dry run: every write for the day, in order, sent nowhere. At work, one runner
sends them, in order:

    def run_pipeline(day, send):
        for step in pipeline(day):
            run(step, send=send)

To fill several days, call it once per day, oldest first, so each day's Saved tables are written
in order. Then read the week with `run(weekly, send=send)`, your own send in place of the
Example database's.

### Export one Lineage for the chain

Pass every Statement of the chain to `export_lineage` together, as [Lineage of a pipeline across
Saved tables](#lineage_of_a_pipeline_across_saved_tables) does. Its drawing follows each Saved
table from the Statement that writes it to the ones that read it, from the raw tables to the
weekly rollup. It puts each writer first, whatever order you pass them in, so its title lists
them in the order they must run:

>>> html_file, markdown_file = export_lineage(weekly, team_day_step, job_day_step,
...                                           to="lineage/pipeline.html")
>>> markdown_file.read_text(encoding="utf-8").splitlines()[0]
'# Lineage: job_day_step, team_day_step, weekly'

Open lineage/pipeline.html in a browser and click a box, such as `weekly`'s starts, to light
up every column it comes from, through both Saved tables. The Markdown file's last line names
the commit of your scripts it describes: on this page that is pinned to 1a2b3c4, and in your
notebook it is your own scripts' git commit, as [Lineage of one
Statement](#lineage_of_one_statement) explains.

## Check it worked

The Example database holds no Saved table, so it can't run mart.team_day's write. It can work
out the same numbers for a day straight from the raw tables, in one Statement:

>>> team_day_from_raw = statement(
...     SELECT(job_owners.team,
...            AS(count_rows(where=equals(job_events.event_type, "start")), "starts"),
...            AS(count_rows(where=equals(job_events.event_type, "finish")), "finishes")),
...     FROM(job_events),
...     JOIN(job_owners, ON=all_of(equals(job_owners.job_id, job_events.job_id),
...                                equals(job_owners.dt, job_events.dt))),
...     WHERE(equals(job_events.dt, "2026-09-24"), equals(job_owners.dt, "2026-09-24")),
...     GROUP_BY(job_owners.team),
... )
>>> run(team_day_from_raw, send=example_database.send)
      team  starts  finishes
0     data       1         1
1  finance       1         0

On 2026-09-24, data's nightly_load started and finished, and finance's invoice_sync started and
is still going. At work, after the pipeline has run, read mart.team_day's 2026-09-24 through
`team_day` with `run`: the two should match.

## Common mistakes

### A Saved table's Table reference changed, but not its write

Say mart.job_day gains a column, the runs that failed. Add it to the Table reference and the old
write no longer fills every column, so the Toolbox refuses it:

>>> job_day = Table(
...     "mart.job_day",
...     columns={"job_id": "bigint", "starts": "bigint", "finishes": "bigint",
...              "fails": "bigint", "dt": "string"},
...     date_partition="dt",
...     key=["job_id", "dt"],
... )
>>> write_job_day("2026-09-24")
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  INSERT_OVERWRITE(job_day): it leaves out fails.
...

Add `AS(count_rows(where=equals(job_events.event_type, "fail")), "fails")` to its `SELECT`.
The table itself must change too. `create_table(job_day, may_exist=True)` does nothing while
the old table exists, and without `may_exist=True` the warehouse refuses to create it, so drop
it with `drop_table(job_day)`, create it again and write its days again, as the gallery's
[Saved table Worked example](examples.html#saved_table) shows in its rebuild step.

### Saving the weekly rollup

A Saved table of weeks looks tidy, but a write fills one day, and a week is seven. Written over
a week, the write is refused when it becomes Hive, before anything is sent:

>>> team_week = Table(
...     "mart.team_week",
...     columns={"team": "string", "starts": "bigint", "finishes": "bigint", "dt": "string"},
...     date_partition="dt",
...     key=["team", "dt"],
... )
>>> to_hive(statement(
...     INSERT_OVERWRITE(team_week),
...     SELECT(team_day.team,
...            AS(sum_of(team_day.starts), "starts"),
...            AS(sum_of(team_day.finishes), "finishes")),
...     FROM(team_day),
...     WHERE(between(team_day.dt, "2026-09-21", "2026-09-27")),
...     GROUP_BY(team_day.team),
... ))
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  INSERT_OVERWRITE(team_week) covers 7 days.
...

Save the days, in mart.team_day, and add them up into weeks when you read them, with
`weekly_rollup`, as the steps do.

### A step that rewrites the table it reads

A tidy-up step that reads mart.team_day and writes mart.team_day again, say to drop a team,
reads its own output. Run twice, it works on rows it has already changed. `export_lineage`
can't draw it either, since its Lineage would lead back into itself:

>>> without_web = statement(
...     INSERT_OVERWRITE(team_day),
...     SELECT(team_day.team, team_day.starts, team_day.finishes),
...     FROM(team_day),
...     WHERE(equals(team_day.dt, "2026-09-24"), not_equals(team_day.team, "web")),
... )
>>> export_lineage(job_day_step, team_day_step, without_web)
Traceback (most recent call last):
...
ValueError:
  What happened:  export_lineage can't draw these Statements, because they go round in a loop: without_web writes mart.team_day, which without_web reads.
...

Leave the team out in the write that fills mart.team_day, `write_team_day`, or write the tidied
rows to a new Saved table of their own.

## Next

- Keep each Saved table's last few days up to date as late rows arrive: [Incremental loads and
  late data](#incremental_loads_and_late_data).
- Share the pieces several Statements need: [Share Building blocks between
  Statements](#share_building_blocks_between_statements).
- The gallery's Worked examples of [`export_lineage`](examples.html#export_lineage) and
  [`show_hive`](examples.html#show_hive).
"""
