"""A layered pipeline

For: Intermediate

## Goal

Build a pipeline in layers, each a Saved table the next one reads: the raw events, then each
job's day, then each team's day, then a weekly rollup read from the team layer. You give each
layer its Table reference and its write, put the day's writes in one list that runs every
writer before the layers that read it, and export one Lineage for the whole chain.

## When you'd use it

When one number goes through several steps, and several notebooks or dashboards read the steps
in between. Each layer is worked out once a day and saved, so its readers read a few saved rows
rather than every raw row again, and each layer can be checked on its own.

## Steps

### Import the Toolbox

The raw layer is two tables of the Example database: `ops.job_events`, what each job's runs did
each day, and `ops.job_owners`, each job's team on each day.

>>> from sqlglot_composer import *
>>> job_events = example_database.job_events
>>> job_owners = example_database.job_owners

### Describe each Saved table

Each layer is a Saved table with a Table reference written by hand, since it doesn't exist until
you create it. mart.job_day holds each job's runs started and finished per day; mart.team_day
adds them up per team, as of each day. At work each goes in a file of its own under
table_references/.

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

### Write each layer's day

Each layer's write is a function of the day it writes. The job layer reads the raw events:

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

The team layer reads the job layer through its Table reference, `job_day`, like any other
table, and takes each job's team from that day's snapshot of owners, as [Look things up as of a
day](#look_things_up_as_of_a_day) does. Adding up the jobs' counts into the team's is safe: a
sum of counts is still the right count.

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

### Read the weekly rollup from the team layer

A write fills one day of its Saved table, the one day its `FROM` table reads, so the layers you
save are days. The weekly rollup is the last layer: a Statement that adds up the team layer's
saved days into weeks whenever you read it, which is quick, since each day holds a row per team.
Read whole weeks, from a Monday to a Sunday:

>>> def team_week(first_day, last_day):
...     return statement(
...         SELECT(AS(week_start(team_day.dt), "week"), team_day.team,
...                AS(sum_of(team_day.starts), "starts"),
...                AS(sum_of(team_day.finishes), "finishes")),
...         FROM(team_day),
...         WHERE(between(team_day.dt, first_day, last_day)),
...         GROUP_BY("week", team_day.team),
...     )
>>> weekly = team_week("2026-09-14", "2026-09-20")

### Put the day's writes in order

A layer must be written after the layers it reads, or it reads a day they haven't written yet,
and nothing would stop it. So one function lists the day's writes in that order, each writer
before its readers, and it is the only place that order is kept:

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

To fill several days, call it once per day, oldest first, so each day's layers are written in
order. Then read the week with `run(weekly, send=send)`, your own send in place of the Example
database's.

### Export one Lineage for the chain

Pass every Statement of the chain to `export_lineage` together. Its drawing follows each Saved
table from the Statement that writes it to the ones that read it, from the raw tables to the
weekly rollup. It puts each writer first, whatever order you pass them in, so its title lists
them in the order they must run:

>>> html_file, markdown_file = export_lineage(weekly, team_day_step, job_day_step,
...                                           to="lineage/pipeline.html")
>>> markdown_file.read_text(encoding="utf-8").splitlines()[0]
'# Lineage: job_day_step, team_day_step, weekly'

Open lineage/pipeline.html in a browser and click a box, such as `weekly`'s starts, to light
up every column it comes from, through both Saved tables.

## Check it worked

The Example database holds no Saved table, so it can't run the team layer. It can work out the
same numbers for a day straight from the raw tables, in one Statement:

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

### A layer's Table reference changed, but not its write

Say the job layer gains a column, the runs that failed. Add it to the Table reference and the
old write no longer fills every column, so the Toolbox refuses it:

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
The table itself must change too: `create_table` refuses while the old one exists, so drop it,
create it again and write its days again, as the gallery's
[Saved table Worked example](examples.html#saved_table) shows in its rebuild step.

### A step that rewrites the table it reads

A tidy-up step that reads mart.team_day and writes mart.team_day again, say to drop a team,
reads its own output. Run twice, it works on rows it has already changed. `export_lineage`
can't draw it either, since its lineage would lead back into itself:

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

Leave the team out in the write that fills the layer, `write_team_day`, or write the tidied rows
to a new layer of their own.

## Next

- Keep each layer's last few days up to date as late rows arrive: [Incremental loads and late
  data](#incremental_loads_and_late_data).
- Share the pieces several layers need: [A library of Building
  blocks](#a_library_of_building_blocks).
- The gallery's Worked examples of [`export_lineage`](examples.html#export_lineage) and
  [`show_hive`](examples.html#show_hive).
"""
