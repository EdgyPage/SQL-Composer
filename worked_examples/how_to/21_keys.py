"""Keys, checked before each write

For: Intermediate

## Goal

Give a table a Key, the columns whose values name exactly one row of it, and let the Toolbox
check it: a write into a Saved table, a real table your own Statements write, whose rows the
Toolbox can't see are one per Key is refused before anything is sent, `check_key` counts the
rows themselves, and Lineage, the record of which table columns feed each output column,
shows each step's Key. A table with no Key, such as ops.team_notes, is written unchecked, and
a join onto it warns.

## When you'd use it

- If you fill in a Table reference, the file that describes one table, write its Key in it.
- If you make a Saved table, give it a Key and let each write be checked against it. Hive
  never checks a Key: a table declared with one takes two rows with the same Key without a
  word. Then every join on that Key repeats rows, and every sum over the join comes out too
  big, far from the write that caused it. The Toolbox checks the Key while the write is
  built, where the mistake is.
- If a table already holds rows, count them against its Key with `check_key`, as Check it
  worked does.
- If you haven't yet, read [Add your tables' references](#add_your_tables_references),
  [Count, join and stay safe](#count_join_and_stay_safe) and [Save a table](#save_a_table)
  first: this how-to needs all three.

## Steps

### 1. Start from the Intermediate Example project

Goal: a Project to work in. An Example project is a Project made for the Example database's
tables, filled in, to read and copy from.

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

Done when the folder you work in holds the Project's admin/, references/ and tables/. Then
step 2.

### 2. Import what the steps call

Goal: the names every step below reads. Import the Toolbox, its project module, the
Project's `query` and `execute` from warehouse.py, which here call the Example database, and
the Project's `ops` Database, a named group of tables:

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> from warehouse import query, execute
>>> from references import ops
>>> job_events, job_owners, team_notes = ops.job_events, ops.job_owners, ops.team_notes

Done when the imports run without an error. Then step 3.

### 3. Read the Keys of the tables you read

Goal: know what names one row of each table. `key=` lists the columns that, together, pick
out one row: no two rows have the same values in all of them. Which columns those are depends
on what a row is, never on how the table is partitioned into Partitions, the slices of rows
that share a value of each partition column.

Each Table reference in the Project's references/ says its Key, such as
references/ops__job_events.py:

- ops.job_events has a row per event, and every event has its own event_id:
  `key=["event_id"]`. It is partitioned by dt, but an event_id names a row on its own, so dt
  isn't in the Key.
- ops.job_owners has a row per job per day, a snapshot of each job each day: one job_id comes
  back on every day, so naming a row takes the job and the day, `key=["job_id", "dt"]`. dt
  is its partition column too; that it is in the Key is because a row needs it.
- ops.team_notes has no columns that name a row, since a team can write the same note twice:
  `key=None`. A table with no Key is fine; what the Toolbox can check of it is less.

Done when you can say each table's Key from what one of its rows is. Then step 4.

### 4. Make the Saved table's Table folder

Goal: the files of a new Saved table. mart.job_day_events will hold one row for each job on
each day: its events and their minutes. Make its Table folder, the folder that holds
everything about one Saved table, and its Table reference with `project.new_table`, as [Save
a table](#save_a_table) shows:

>>> project.new_table("mart.job_day_events")
Made tables/mart__job_day_events/: mart__job_day_events.ipynb and lineage/, from
admin/templates/saved_table.py.
Wrote references/mart__job_day_events.py: project.reference_from_logic writes it.

Done when `project.new_table` says it made tables/mart__job_day_events/. Then step 5.

### 5. Give the Saved table a Key

Goal: a Table reference that says what names one row. Fill in its Table reference. A job has
a row on every day, so its Key is the job and the day, as ops.job_owners' is:

The file `references/mart__job_day_events.py`, after you fill it in:

    \"\"\"mart.job_day_events - one row per job and day: its events and their minutes.\"\"\"
    from sqlglot_composer import Table

    job_day_events = Table(
        "mart.job_day_events",
        columns={"job_id": "bigint", "events": "bigint", "minutes": "bigint", "dt": "string"},
        partitioned_by=["dt"],
        key=["job_id", "dt"],
        location="/data/your_team/mart.db/job_day_events",
    )

Done when references/mart__job_day_events.py says `key=["job_id", "dt"]`. Then step 6.

### 6. Refresh the Database module

Goal: the new table, by its name. `project.refresh_reference_sheet()` writes the Database
module references/mart.py again from the Table references, as it does once you fill one in,
so `from references import mart` gives the new table by its name:

>>> project.refresh_reference_sheet()
Wrote references/reference_sheet.csv: 54 rows, 13 tables.
Wrote references/mart.py: from references import mart gives mart.budget_overruns,
    mart.job_day_costs, mart.job_day_events, mart.job_day_facts, mart.job_events_checks,
    mart.job_notes, mart.team_days and mart.team_failures.
Restart the kernel of a notebook that imported references, to see a table added since.
>>> from references import mart
>>> job_day_events = mart.job_day_events  # -> Table

Done when references/mart.py lists mart.job_day_events. Then step 7.

### 7. Write a Statement that shows its Key

Goal: a write the Toolbox can see is one row per Key.
`GROUP_BY(job_events.job_id, job_events.dt)` makes one row for each job and day, so the
Toolbox can see the Key holds, and builds the write. It fills each day's Partition from the
rows' own dt, which SELECT may name anywhere: the Toolbox puts it last, where Hive reads it
from, and `show_hive` adds the Session setting, a Hive SET sent before it, that such a write
needs:

>>> def write_job_day_events(first_day: str, last_day: str) -> Statement:
...     return statement(
...         INSERT_OVERWRITE(job_day_events),
...         SELECT(job_events.job_id, job_events.dt, AS(count_rows(), "events"),
...                AS(sum_of(job_events.minutes), "minutes")),
...         FROM(job_events),
...         WHERE(between(job_events.dt, first_day, last_day)),
...         GROUP_BY(job_events.job_id, job_events.dt),
...     )
>>> write = write_job_day_events("2026-09-22", "2026-09-24")  # -> Statement
>>> text = show_hive(write)
-- The Session setting "dynamic_partitions": this write fills dt from its rows.
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
INSERT OVERWRITE TABLE mart.job_day_events PARTITION(dt)
SELECT
  job_events.job_id,
  COUNT(*) AS events,
  SUM(job_events.minutes) AS minutes,
  job_events.dt
FROM ops.job_events AS job_events
WHERE
  job_events.dt BETWEEN '2026-09-22' AND '2026-09-24'
GROUP BY
  job_events.job_id,
  job_events.dt;

Done when `show_hive(write)` prints the INSERT OVERWRITE with its GROUP BY. Then step 8.

### 8. See a write that can't show its Key refused

Goal: know what the check stops. Leave GROUP_BY out, and the write would save one row for each
event: a job with four events that day would have four rows with the same Key. A Guard, a
check that refuses a Statement that would give a wrong result, refuses it as it is built:

>>> statement(
...     INSERT_OVERWRITE(job_day_events),
...     SELECT(job_events.job_id, job_events.dt, AS(job_events.event_id, "events"),
...            AS(job_events.minutes, "minutes")),
...     FROM(job_events),
...     WHERE(between(job_events.dt, "2026-09-22", "2026-09-24")),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  INSERT_OVERWRITE(job_day_events) can't show that each row it writes has a Key
                  (job_id, dt) of its own: job_events' rows are told apart by event_id, not by
                  job_id, dt.
...

ops.job_events' own Key is event_id: without GROUP_BY, the rows written are its rows, one for
each event, and nothing makes them one for each job and day.

Done when the GuardRefused names the Key (job_id, dt). Then step 9.

### 9. Show a Key in another way

Goal: a Key the Toolbox sees without GROUP_BY. The Toolbox looks at how a write makes its rows.
Each of these shows a Key:

- **GROUP_BY over the Key's columns**, as above: one row for each group.
- **SELECT_DISTINCT**: one row for each different row. A column whose value another column
  already fixes doesn't count: one `job_events.event_id` always comes with the same
  `job_events.job_id`, so SELECT_DISTINCT of both makes one row for each event.
- **row_number(...) kept at 1 for each Key**, in a Derived table, a Statement named so another
  can read from it, as [The latest row of each group](#latest_row_of_each_group) does: one
  row for each `PARTITION_BY=` value.
- **The rows of the table in FROM, by its own Key**, when SELECT returns that Key's columns,
  and each join matches its joined table's whole Key, so each row from FROM meets at most one
  row of the joined table. A SEMI_JOIN or ANTI_JOIN keeps the Key whatever its ON= matches,
  since it never repeats a row; a FULL_JOIN loses it, since either side's columns may be NULL.
  [Semi-, anti- and full joins](#semi_anti_and_full_joins) shows each.

Here the last two together: each job's last event of each day, numbered in a Derived table,
then joined to ops.job_owners on its whole Key, the job and the day, which keeps one row for
each job and day:

>>> numbered = derived("numbered", statement(  # -> Table
...     SELECT(job_events.job_id, job_events.dt, job_events.event_type,
...            AS(row_number(PARTITION_BY=[job_events.job_id, job_events.dt],
...                          ORDER_BY=descending(job_events.event_id)), "last_first")),
...     FROM(job_events),
...     WHERE(between(job_events.dt, "2026-09-23", "2026-09-24")),
... ))
>>> last_events = statement(  # -> Statement
...     SELECT(numbered.job_id, numbered.dt, numbered.event_type, job_owners.team),
...     FROM(numbered),
...     JOIN(job_owners, ON=all_of(equals(job_owners.job_id, numbered.job_id),
...                                equals(job_owners.dt, numbered.dt),
...                                between(job_owners.dt, "2026-09-23", "2026-09-24"))),
...     WHERE(equals(numbered.last_first, 1)),
... )

Done when `last_events` builds without a Warning. Then step 10.

### 10. Read each step's Key in its Lineage

Goal: see where each Statement keeps or loses its Key. `export_lineage` marks each column
that is part of a Key "in the Key", and its Markdown file lists each step's Key, or where it
lost one, and whether a write's Key holds:

>>> html_file, markdown_file = export_lineage(last_events, write,  # -> tuple[Path, Path]
...                                           to="lineage/keys.html")
>>> for keys in markdown_file.read_text(encoding="utf-8").split("### Keys")[1:]:
...     print(keys.split("###")[0].strip().split("\\n\\n")[1])
- derived('numbered', ...): Key (job_id, dt, last_first), since row_number(...) numbers the rows
  of each job_id, dt.
- last_events: Key (job_id, dt), since numbered's rows are told apart by job_id, dt, last_first,
  with last_first held to one value.
- write: Key (job_id, dt), since GROUP_BY makes one row for each job_id, dt.
- mart.job_day_events' Key (job_id, dt) holds: each row written has its own.

Done when the list ends with mart.job_day_events' Key holding. Then step 11.

### 11. Let through rows you know are one per Key

Goal: a write whose rows are one per Key for a reason the Toolbox can't see. Sometimes you
know more than the Toolbox can see: here, that a job has at most one finish event a day, a
habit of how its runs are scheduled that no Table reference says. Then `unproven_key=True`
on the write lets it through:

>>> finishes = statement(  # -> Statement
...     INSERT_OVERWRITE(job_day_events, unproven_key=True),
...     SELECT(job_events.job_id, job_events.dt, AS(job_events.event_id, "events"),
...            AS(job_events.minutes, "minutes")),
...     FROM(job_events),
...     WHERE(between(job_events.dt, "2026-09-22", "2026-09-24"),
...           equals(job_events.event_type, "finish")),
... )

Write it only when you are sure, and check the days with `check_key` once they are written.
`INSERT_INTO` is checked the same way, on the rows it adds; the rows already there may share a
Key with them, which only `check_key` can find.

Done when `finishes` builds without a refusal. Then step 12.

### 12. Create the table with its Key

Goal: the Key in the table's CREATE TABLE. `create_table` makes the table with its Key:

>>> text = show_hive(create_table(job_day_events))
CREATE EXTERNAL TABLE mart.job_day_events (
  job_id BIGINT,
  events BIGINT,
  minutes BIGINT,
  PRIMARY KEY (job_id, dt) DISABLE NOVALIDATE
)
PARTITIONED BY (
  dt STRING
)
STORED AS ORC
LOCATION '/data/your_team/mart.db/job_day_events';

`DISABLE NOVALIDATE` tells Hive to keep the Key as information only: Hive never checks it,
which is why the Toolbox does.

Done when the Hive shows `PRIMARY KEY (job_id, dt) DISABLE NOVALIDATE`. Then step 13.

### 13. Write a table with no Key

Goal: a write into a table that declares no Key. Nothing is checked against a Key a table
doesn't have. The Example project's mart.job_notes
says `key=None`, so its notebook's write is built without a Key check, and needs no
`unproven_key=True`. The table has no partition column, so the write replaces the whole table:

>>> notes_write = statement(  # -> Statement
...     INSERT_OVERWRITE(mart.job_notes),
...     SELECT(job_owners.job_id, team_notes.team, team_notes.note, team_notes.written_on),
...     FROM(team_notes),
...     JOIN(job_owners, ON=all_of(equals(job_owners.team, team_notes.team),
...                                equals(job_owners.dt, team_notes.written_on),
...                                between(job_owners.dt, "2026-09-11", "2026-09-24")),
...          many_matches=True),
... )

Done when `notes_write` builds without a refusal. Then step 14.

### 14. Join onto a table with no Key

Goal: a join you have said may match several rows. A join onto a table with no Key is another
matter: the Toolbox can't tell whether one row matches or several, so it gives a Warning, a
check that lets the Statement through but says why a number may come out wrong, as it does
for a join that doesn't match a Key whole:

>>> notes_per_job = statement(  # -> Statement
...     SELECT(job_owners.job_id, team_notes.note),
...     FROM(job_owners),
...     JOIN(team_notes, ON=equals(team_notes.team, job_owners.team)),
...     WHERE(equals(job_owners.dt, "2026-09-24")),
... )

In a notebook, the Warning shows under the cell, at your own line, and doesn't stop anything:
it says that team_notes declares no Key, so the Toolbox can't tell whether one row matches or
several. Here several rows are what you want, a row for each note of each job's team, so say so
with `many_matches=True`, as `notes_write` does. A count or a sum over such a join counts each
job once per note: to count each job once, group the notes first.

Done when the join says `many_matches=True`, or groups the notes first. Then check it worked,
below.

## Check it worked

The Toolbox's check sees how the rows are made; `check_key` counts the rows themselves. Run it
on a Saved table after its first writes, and on any table you join to by its Key. The Example
database holds no mart.job_day_events, but the write's rows come from its SELECT, which it can
run: one row for each job and day.

>>> per_job_day = statement(
...     SELECT(job_events.job_id, job_events.dt, AS(count_rows(), "events")),
...     FROM(job_events),
...     WHERE(between(job_events.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_events.job_id, job_events.dt),
... )
>>> rows = run_query(per_job_day, query)  # -> DataFrame
>>> bool(rows.duplicated(["job_id", "dt"]).any())
False

On a table that holds rows already, `check_key` counts them, on the rows `where=` picks: a
partitioned table is read only where you say, as any read is.

>>> check_key(job_owners, query=query,
...           where=equals(job_owners.dt, "2026-09-24"))  # -> Verdict
ops.job_owners: the key (job_id, dt) holds where job_owners.dt = '2026-09-24'.

Before you go on, check that:

- the write's rows show no repeated job_id and dt: the check above gives `False`;
- the Lineage's Markdown file says mart.job_day_events' Key (job_id, dt) holds;
- `check_key` says the key holds on each table you join to by its Key.

## Common mistakes

### Grouping by more than the Key

A GROUP_BY with one more column makes one row for each event type, not for each job and day:

>>> statement(
...     INSERT_OVERWRITE(job_day_events),
...     SELECT(job_events.job_id, job_events.dt, AS(count_rows(), "events"),
...            AS(sum_of(job_events.minutes), "minutes")),
...     FROM(job_events),
...     WHERE(between(job_events.dt, "2026-09-22", "2026-09-24")),
...     GROUP_BY(job_events.job_id, job_events.dt, job_events.event_type),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  INSERT_OVERWRITE(job_day_events) can't show that each row it writes has a Key
                  (job_id, dt) of its own: GROUP_BY groups by job_events.event_type, which
                  SELECT leaves out, so nothing makes its rows one for each job_id, dt.
...

Decide which is meant: if a row is one per event type, add event_type to the Key; if a row is
one per job and day, group by the job and the day alone.

### A join that can repeat rows

A join onto a table with no Key may add several rows to one, and `many_matches=True` silences
only the join's Warning. The write's Key check stays: mart.job_day_events' Key still says one
row for each job and day, and these rows can repeat one:

>>> statement(
...     INSERT_OVERWRITE(job_day_events),
...     SELECT(job_owners.job_id, job_owners.dt, AS(job_owners.owner, "events"),
...            AS(job_owners.owner, "minutes")),
...     FROM(job_owners),
...     JOIN(team_notes, ON=equals(team_notes.team, job_owners.team), many_matches=True),
...     WHERE(equals(job_owners.dt, "2026-09-24")),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  INSERT_OVERWRITE(job_day_events) can't show that each row it writes has a Key
                  (job_id, dt) of its own: JOIN(team_notes, ON=...) can match several team_notes
                  rows to one row, and team_notes declares no Key, so nothing makes its rows one
                  for each job_id, dt.
...

Group the joined rows by the Key, one row for each job and day, as [Count, join and stay
safe](#count_join_and_stay_safe) shows.

### Checking every Partition by leaving where= out

`check_key` reads the rows it checks, so on a partitioned table it needs `where=`, as any read
does:

>>> check_key(job_events, query=query)
Traceback (most recent call last):
...
ValueError:
  What happened:  check_key(job_events): ops.job_events is partitioned, and nothing says which
                  Partitions to check.
...

Pass `where=equals(job_events.dt, "2026-09-24")`, or `reads_all_partitions=True` for a table
small enough to read whole. A table with no Key, such as ops.team_notes, has nothing to check,
and `check_key` says so.

### Silencing the check with unproven_key=True

`unproven_key=True` doesn't make the rows one per Key: it only stops the Toolbox saying they
might not be. Make the rows one per Key with GROUP_BY, SELECT_DISTINCT or row_number first,
and keep `unproven_key=True` for rows you know are one per Key.

## Next

- [Count, join and stay safe](#count_join_and_stay_safe): the repeated-rows Warning, which reads
  the Keys of the tables a Statement joins.
- [The latest row of each group](#latest_row_of_each_group): row_number, kept at 1 for each Key.
- [Semi-, anti- and full joins](#semi_anti_and_full_joins): which joins keep a Key.
- The gallery's [`INSERT_OVERWRITE`](examples.html#INSERT_OVERWRITE) and
  [`check_key`](examples.html#check_key).
"""
