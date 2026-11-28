"""Load a History table's past days

For: Intermediate

## Goal

Make a table that keeps its days usable from its first day. The words this page uses, one at a
time:

- A table's **kind** says what each of its writes does to the rows already there.
- A **Rebuilt table** is replaced whole by each write, so its first write leaves it complete.
- A **History table** keeps the rows already there: each write adds rows, or replaces some,
  such as one day's **Partition**, the rows that share one value of its partition column.
- A new History table, in dev or in prod, holds only the days its writes have added since it
  was made, so the Toolbox loads its past days once, before its first write: its **Seed**.
- The kind is a **Decision**, one thing about one table only you decide. new_table and
  convert propose it from the table's write; you accept it, or answer it, in a Workflow
  notebook's decisions cell.
- The table's **Table reference**, the file in references/ that describes its columns, holds
  its kind on its KIND line, and, for a History table, how far back its Seed goes on its
  SEED line: `{"months": 1}`, one calendar month back from the newest day, is proposed.

The step that writes the table runs its Seed for you, and `project.check(query=query)` warns
while a day it should have loaded is missing.

## When you'd use it

- If each write of a table replaces one day's Partition, or adds rows, answer its kind
  "history", as step 5 does: its Seed loads its past days.
- If each write replaces the whole table, answer "rebuilt": its first write is complete, and
  it has no Seed. Answered "rebuilt", a table's SEED line is taken out, even one proposed
  while its kind was open, as step 4's is.
- If a kind is proposed, accept it with "proposed"; if nothing is proposed, as for a write that
  fills its Partitions from its rows' own values, PARTITION (dt), answer it yourself, as step
  5 does.
- If you want more days, answer "seed" with more months, such as `{"months": 3}`, or with a
  range, as Seed limits, in full, in [Convert someone else's
  Hive](#convert_someone_elses_hive) says.
- If `project.check()` names a kind or Seed left open, as `project.upgrade()` leaves some,
  answer it by the table's name in the decisions cell of the Workflow you run next on that
  table, or from admin/check_project.ipynb with `project.write_decisions(...)`, as step 2
  shows.
- If your write works its day out from today, with `last_n_days`, a Run value starting from
  `today()`, or CURRENT_DATE in Hive, its Seed runs it as of each past day, as step 6 shows;
  if it reads a day typed in, it has no Seed.
- If the table is converted from someone else's Hive, its Seed copies its original's rows in
  place of running its write: [Convert someone else's Hive](#convert_someone_elses_hive) shows
  it.

## Steps

### 1. Start from the Intermediate Example project

Goal: a Project whose tables read a table of days. Work in your own Project, at its top. This
page works in a copy of the Intermediate Example project, which the download's Example projects
page shows file by file: `example_project("intermediate")` makes that copy in the folder the
page runs in, a line you leave out in your own Project. Fill in DEV's "location_root" in
admin/databases.py, the folder your Dev Database's tables go under, as [Set your Database
settings](#set_your_database_settings) shows; this page stands in for your edit:

>>> from pathlib import Path
>>> example_project("intermediate")
>>> from sqlglot_composer import project, run_execute
>>> from warehouse import connect, execute, query
>>> connect(conn)
>>> databases = Path("admin/databases.py")
>>> _ = databases.write_text(databases.read_text(encoding="utf-8").replace(
...     '"<DEV_LOCATION_ROOT>"', '"/data/dev"'), encoding="utf-8")

`conn` is the Example database's connection on this page, made-up tables the Toolbox's makers
keep, which the download doesn't hold. At work it is your team's connection, as each
notebook's `connect(...)` line gives it.

Done when `connect(conn)` runs without an error. Then step 2.

### 2. Read each table's kind

Goal: know what each kind looks like, answered and open. Each Table reference holds its kind
on its KIND line, and a History table its SEED line:

>>> for path in sorted(Path("references").glob("mart__*.py")):
...     for line in path.read_text(encoding="utf-8").splitlines():
...         if line.startswith(("KIND = ", "SEED = ")):
...             print(f"{path.stem}: {line}")
mart__budget_overruns: KIND = "history"  # answered, proposed history: its INSERT OVERWRITE replaces one Partition, keeping the others
mart__budget_overruns: SEED = {}  # TODO: nothing proposed: project.upgrade() reads no Partitions, so nothing says which partition column, if any, holds dates
mart__job_day_costs: KIND = None  # TODO: nothing proposed: its INSERT OVERWRITE fills dt from its rows' own values, PARTITION (dt), so it may replace every Partition or only some
mart__job_day_facts: KIND = "history"  # answered, nothing proposed: its INSERT OVERWRITE fills dt from its rows' own values, PARTITION (dt), so it may replace every Partition or only some
mart__job_day_facts: SEED = {"months": 1}
mart__job_events_checks: KIND = None  # TODO: nothing proposed: its INSERT OVERWRITE fills dt from its rows' own values, PARTITION (dt), so it may replace every Partition or only some
mart__job_hours: KIND = "rebuilt"  # answered, proposed rebuilt: it is a query alone, which each write writes whole
mart__job_notes: KIND = "rebuilt"  # answered, proposed rebuilt: its INSERT OVERWRITE names no Partition, so it replaces the whole table
mart__team_days: KIND = None  # TODO: nothing proposed: its INSERT OVERWRITE fills dt from its rows' own values, PARTITION (dt), so it may replace every Partition or only some
mart__team_failures: KIND = None  # TODO: nothing proposed: its INSERT OVERWRITE fills dt from its rows' own values, PARTITION (dt), so it may replace every Partition or only some

What each line says:

- A kind is proposed from what the write does, never from what its query works out.
  mart.budget_overruns writes PARTITION (region = 'eu'), one Partition, keeping the
  others: History. mart.job_notes names no Partition, so each write replaces the whole table:
  Rebuilt. mart.job_hours is a query alone: Rebuilt.
- A line's comment says which of three it is. `# TODO:` marks a Decision still open, which
  promote waits on: `KIND = None` is a kind with nothing proposed. `# answered,` marks a kind
  made: what follows it is what was proposed when it was asked, kept for the record, so
  `answered, nothing proposed` means you answered it yourself, since nothing was proposed.
  `# proposed`, as step 4 shows, marks a proposal the Toolbox made and uses as it is, which
  blocks nothing. A line with no comment, as mart.job_day_facts's SEED, is an answer you
  wrote.
- A write that fills its Partitions from its rows' own values, PARTITION (dt), may replace
  every Partition or only some, so nothing is proposed. mart.job_day_facts writes its last 3
  days that way and keeps the rest: it was answered "history", with a SEED of one month.
- mart.budget_overruns was written before 8.10, so it had no SEED: `project.upgrade()` asked
  for one. It reads no Partitions, so it proposed nothing, and the table is partitioned by
  region alone, which holds no dates: `{"months": 1}` can't apply, and `{}`, every region,
  is the answer that fits.

The four `KIND = None` and that SEED block nothing in dev: your notebooks still write those
tables, and only promote refuses them, as each Decision is made before a table reaches prod.
`project.check()` names each, with where to answer it:

>>> project.check()
Every Table folder, Table reference, Building block and Scheduled run is registered, and each
    one registered is there.
Open in a Table reference, which only promote waits on: each table's kind, Rebuilt or
    History, or its Seed, below. Answer each by the table's name in the decisions cell of the
    Workflow you run next on it, or in admin/check_project.ipynb, such as
    project.write_decisions({"mart.x": {"kind": "history"}}).
  references/mart__budget_overruns.py: mart.budget_overruns' seed, nothing proposed
  references/mart__job_day_costs.py: mart.job_day_costs' kind, nothing proposed
  references/mart__job_events_checks.py: mart.job_events_checks' kind, nothing proposed
  references/mart__team_days.py: mart.team_days' kind, nothing proposed
  references/mart__team_failures.py: mart.team_failures' kind, nothing proposed
Done: each convert batch below.
  admin/workflows/convert/convert.ipynb, job_hours: every table the batch wrote passed its
    compare, and its folder is admin/workflows/convert/finished/job_hours/.
  admin/workflows/convert/convert.ipynb, team_failures: every table the batch wrote passed its
    compare, and its folder is admin/workflows/convert/finished/team_failures/.

Done when you can tell an answered KIND from an open one. Then step 3.

### 3. Make a table that writes yesterday

Goal: a History table whose write works out its day from today. Run the new_table Workflow's
first step for mart.job_day_events, each job's events on one day:

>>> project.new_table("mart.job_day_events")
Made tables/mart__job_day_events/: mart__job_day_events.ipynb and lineage/, from
admin/templates/saved_table.py.
Wrote references/mart__job_day_events.py: project.reference_from_logic writes it.

Its write reads yesterday, worked out from today each time the table is written, so a write
run each morning writes the day before. `last_n_days(job_events.dt, 1)` is that day; on this
page today is 2026-09-25:

>>> from sqlglot_composer import last_n_days, today
>>> from references.ops__job_events import job_events
>>> last_n_days(job_events.dt, 1)
job_events.dt = '2026-09-24'

The day is worked out when the logic runs, so READS below holds 2026-09-24 today. That is no
fixed day: `last_n_days` counts from the Toolbox's `today()`, and the Seed runs your logic
again for each past day with `today()` set to that day, so READS is worked out again for each.
A Run value starting from `today()`, or CURRENT_DATE in Hive, counts the same way. Python's own
date.today(), from its datetime module, doesn't: it gives the computer's day whatever the Seed asks, so use
`today()`.

Fill in its notebook's logic with it:

The file `tables/mart__job_day_events/mart__job_day_events.ipynb`, after you fill it in:

    # %% [markdown]
    # # mart.job_day_events
    #
    # Each job's events on one day, yesterday's, written each day into that day's Partition.

    # %%
    # 1. The Project and your query
    import pathlib
    import sys
    sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

    from sqlglot_composer import show_hive
    from warehouse import connect, query

    # %%
    # logic
    # 2. The logic: imports, the rows it reads, and functions only
    from sqlglot_composer import (
        AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, Clause, Statement, count_rows,
        create_table, last_n_days, statement,
    )
    from references.mart__job_day_events import job_day_events  # this table's own Table reference
    from references.ops__job_events import job_events

    # The rows write() reads: yesterday's, worked out from today each time it is written.
    READS = last_n_days(job_events.dt, 1)

    # This table's partition columns, in the order its SELECT gives them, last.
    PARTITIONED_BY = ["dt"]


    def create() -> Statement:
        \"\"\"Step 1: create mart.job_day_events from its Table reference, if it isn't there yet.\"\"\"
        return create_table(job_day_events, may_exist=True)


    def rows() -> list[Clause]:
        \"\"\"The clauses preview and write share: each job's events on the day READS picks.\"\"\"
        return [
            SELECT(job_events.job_id, AS(count_rows(), "events"), job_events.dt),
            FROM(job_events),
            WHERE(READS),
            GROUP_BY(job_events.job_id, job_events.dt),
        ]


    def preview() -> Statement:
        \"\"\"Step 2: the rows write() would save, as a SELECT to run and check first.\"\"\"
        return statement(*rows())


    def write() -> Statement:
        \"\"\"Step 3: save yesterday's rows, replacing that day's Partition alone.\"\"\"
        return statement(INSERT_OVERWRITE(job_day_events), *rows())

    # %%
    # 3. Try it: the Hive of each step
    show_hive([create(), write()])

Done when the notebook's logic is saved. Then step 4.

### 4. Write its Table reference from the logic

Goal: its Table reference, with its kind and its Seed to answer. The Workflow's step 3 writes
it from the logic, through your query, which reads the Partitions of the table the write reads
its days from:

>>> print(project.reference_from_logic("mart.job_day_events", query=query))
Wrote references/mart__job_day_events.py from its logic: job_id, events and dt, partitioned by dt.
...
Answer each open Decision in the new_table Workflow's decisions cell: mart.job_day_events: kind: Rebuilt or History table, nothing proposed, as its INSERT OVERWRITE fills dt from its rows' own values, PARTITION (dt), so it may replace every Partition or only some: answer "rebuilt" if each write replaces the whole table, "history" if it keeps the rows already there.
>>> reference = Path("references/mart__job_day_events.py")
>>> for line in reference.read_text(encoding="utf-8").splitlines():
...     if line.startswith(("KIND = ", "SEED = ")):
...         print(line)
KIND = None  # TODO: nothing proposed: its INSERT OVERWRITE fills dt from its rows' own values, PARTITION (dt), so it may replace every Partition or only some
SEED = {"months": 1}  # proposed: dt holds dates in ops.job_events

Its write fills dt from its rows, so no kind is proposed, and its kind is the one Decision
open. SEED is proposed already, though the kind is still open: dt holds dates in
ops.job_events, the table it reads its days from, so a month of them is proposed, marked
`# proposed`, which blocks nothing. What happens to it hangs on the kind you answer next:
answered "history", it stays, a proposal used as it is; answered "rebuilt", the SEED line is
taken out, as a Rebuilt table has no Seed. Above each line, its comment says what it takes.

Done when the KIND line is open and the SEED line proposed. Then step 5.

### 5. Answer its kind and its Seed

Goal: the table a History table, its Seed a month. Write each answer in the new_table
Workflow notebook's decisions cell, DECISIONS, by the table's name; this page stands in for
the cell and for its step, which writes each answer into the Table reference:

>>> DECISIONS = {"mart.job_day_events": {"kind": "history", "seed": {"months": 1}}}
>>> print(project.write_decisions(DECISIONS, tables=["mart.job_day_events"]))
Wrote 2 answers into references/mart__job_day_events.py.
...
Each Decision of mart.job_day_events is made.
>>> for line in reference.read_text(encoding="utf-8").splitlines():
...     if line.startswith(("KIND = ", "SEED = ")):
...         print(line)
KIND = "history"  # answered, nothing proposed: its INSERT OVERWRITE fills dt from its rows' own values, PARTITION (dt), so it may replace every Partition or only some
SEED = {"months": 1}

The answers, by their kind:

- "kind": "history", since each write replaces one day and keeps the rest. Where a kind is
  proposed, "proposed" accepts it, and under "all_tables" it accepts each table's.
- "seed": `{"months": 1}` loads one calendar month back from the newest day the table it reads
  holds, both ends included, by its partition column whose every value is a date: from
  ops.job_events' newest, 2026-09-24, the days 2026-08-24 to 2026-09-24, but for a day the
  table's first write writes, which step 6 leaves to it. `{"months": 3}` loads three months.
  Left unanswered, the proposal is used all the same, as any line marked `# proposed` is;
  answered, it loses its mark.

Done when it says `Each Decision of mart.job_day_events is made.` Then step 6.

### 6. See the days its Seed loads

Goal: the Seed's days seen before anything is sent. The new_table Workflow's write step starts
with `project.seed_tables`, which, given no execute, sends nothing and shows what it would
send. A table with no original runs its own write once for each past day, oldest first. The
days the report names are the dt days written, and each is run as of the day after it, so
`last_n_days` gives that day as yesterday:

>>> said = repr(project.seed_tables(["mart.job_day_events"], query=query))  # -> str
>>> print("\\n".join(said.splitlines()[:14]))
mart.job_day_events: its Seed, its write run as of each past day, oldest first, dt from 2026-08-24 to 2026-09-23, each run as of the day after:
would send: SET hive.exec.dynamic.partition=true
would send: SET hive.exec.dynamic.partition.mode=nonstrict
would send: INSERT OVERWRITE TABLE mart.job_day_events PARTITION(dt)
would send: SELECT
would send:   job_events.job_id,
would send:   COUNT(*) AS events,
would send:   job_events.dt
would send: FROM ops.job_events AS job_events
would send: WHERE
would send:   job_events.dt = '2026-08-24'
would send: GROUP BY
would send:   job_events.job_id,
would send:   job_events.dt

As in step 2, `repr(...)` gives the report as a str, so this page prints its first 14 lines.
The same write follows for each day to 2026-09-23, 31 in all: ops.job_events' newest day is
2026-09-24, and the month back from it starts on 2026-08-24. 2026-09-24 is left out: its run
would be as of today, 2026-09-25, and that run is the table's first write, step 7's, which
follows the Seed, so no day is written twice. Each run is the write's own Hive, its day alone
changed, so each writes the one Partition a run on the morning after writes.

A write whose day is typed in has no Seed of this kind: each run would write the same rows.
mart.job_day_facts reads `DAY = "2026-09-24"`, so its first write loads its days:

>>> print(project.seed_tables(["mart.job_day_facts"], query=query))
mart.job_day_facts: no Seed: its write reads no today, as nothing in it counts from today(): not last_n_days, a Run value starting from today(), nor CURRENT_DATE in its Hive. So each day's run would write the same rows, and its first write loads them.

Done when the first line names the days from 2026-08-24 to 2026-09-23. Then step 7.

### 7. Write the table, its Seed first

Goal: the table's past days in the warehouse, then its first write. The new_table Workflow's
write step, given your execute, creates the table, sends the Seed, then the table's write. Its
cell is these three lines, for each table its names cell's TABLES names, here
mart.job_day_events; at work you run that cell:

    run_execute(project.load("mart.job_day_events").create(), execute)
    print(project.seed_tables(["mart.job_day_events"], query=query, execute=execute))
    project.run_tables(tables=["mart.job_day_events"], execute=execute)

The Example database can't be written to, so this page sends none of them. At work, the
report starts with the line step 6 shows, then says how many days were loaded and which, each
run of days in a row as one range, then a line for each day that wasn't. Say ops.job_events
held no rows on 2026-09-15, and the warehouse refused 2026-09-20's run. The report ends with
these three lines, one report:

- `Seeded mart.job_day_events: 29 days loaded of 31, dt from 2026-08-24 to 2026-09-14, from
  2026-09-16 to 2026-09-19 and from 2026-09-21 to 2026-09-23.`
- `dt = 2026-09-20: not loaded: Error while compiling statement: FAILED: ...`, a day the
  warehouse refused, with the first line of its error;
- `dt = 2026-09-15: no rows, its empty Partition kept`, a day that wrote no rows.

Where several days in a row wrote no rows, in another table's report, one line names them
all, such as `dt from 2026-08-24 to 2026-08-30: no rows, each empty Partition kept`.

A day that fails doesn't stop the rest. Then the table's first write, as of today, writes
2026-09-24. The Seed runs only while the table holds no Partition, so the step run again
loads nothing twice: it says
`mart.job_day_events: no Seed: it holds rows already, so it was seeded, or written, before.`

Done when the report names the days loaded. Then step 8.

### 8. Check the days it holds

Goal: a missing day you can't forget. admin/check_project.ipynb runs `project.check`, given
your query, which reads the days each History table with a Seed holds, once admin/sent.csv
records it written, and warns of each day its Seed should have loaded and it lacks, or holds
with no rows. It stops nothing. On this page neither History table with SEED answered is read:

- mart.job_day_events isn't written yet: admin/sent.csv, which records each Statement your
  execute sent, holds no write of it, since this page sent none. Its Seed runs at its first
  write, so there is nothing to check before.
- mart.job_day_facts is written, but has no Seed, as step 6 shows: there are no days to count
  for it, so its Partitions are never read.

So the check gives no Warning, and no line saying a table's days couldn't be read:

>>> said = repr(project.check(query=query))  # -> str
>>> [line for line in said.splitlines() if line.startswith(("Warning", "Not checked"))]
[]

At work, once step 7 has run, the two days its report named give a Warning, until each is
written: `Warning: mart.job_day_events lacks 2 of the 31 days its Seed loads: 2026-09-15 (no
rows) and 2026-09-20. That stops nothing, but what reads it finds no rows for those days until
each is written.` Write a missing day as you write any day, with a write as of the day after
it. A table whose Partitions your query couldn't read is named on a line starting `Not checked
for the days its Seed loads:`, with what your query said. `project.check()`, with no query,
reads nothing of the warehouse, and gives no such Warning.

Done when the check gives no Warning you haven't dealt with. Then check it worked, below.

## Check it worked

Before you go on, check that:

- references/mart__job_day_events.py says `KIND = "history"  # answered, ...` and
  `SEED = {"months": 1}`;
- the Seed's first line, step 6's, names dt from 2026-08-24 to 2026-09-23;
- at work, the Seed's report names the days loaded, and each day not loaded;
- at work, `project.check(query=query)` gives no Warning for the table, or you have written
  each day it names;
- `project.check()` names no kind or Seed left open for a table you will promote.

## Common mistakes

### Answering "rebuilt" for a table of days

A table answered Rebuilt has no Seed, so a daily table answered so starts with one day, and
nothing warns that the rest are missing. If each write replaces one day and keeps the rest,
answer "history".

### Typing the day in

A write that reads `"2026-09-24"` writes that day on every run, so its Seed can't run it for
each past day, and says so, as mart.job_day_facts's does in step 6. Work the day out from
today, with `last_n_days`, or with a Run value, a function of yours that the Toolbox calls
each time the table is written, starting from `today()`, never from Python's
date.today().

### Expecting the Seed to run again

The Seed runs once, while the table holds no Partition. To load a day it missed, write that
day, as `project.check(query=query)` names it, rather than seeding again.

## Next

- [Convert someone else's Hive](#convert_someone_elses_hive): a converted table's Seed, copied
  from its original, and Seed limits by partition column.
- [Follow a Workflow](#follow_a_workflow): every Workflow's steps, the new_table Workflow's
  among them.
"""  # noqa: E501 - the lines a Table reference and a Seed's report hold, shown whole
