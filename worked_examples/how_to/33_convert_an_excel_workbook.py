"""Convert an Excel workbook

For: Intermediate

## Goal

Turn an Excel workbook's calculations into your own code: its formulas, its Power Query and its
PivotTable, each a Saved table in your Dev Database, the database where you create and write
tables of your own. You give the workbook to the convert Workflow, beside or in place of Hive
scripts, and it reads what reads what in the workbook. Each calculation that nothing else in
the workbook reads, here the PivotTable, is a final: it becomes a Saved table, its Hive built
from the formulas and the query it reads. The Workbook check then runs that Hive on this
computer, over the workbook's own rows, and compares what it gives with the values the workbook
shows. What only you can decide, such as the table's name and what to do with the PivotTable's
slicer, is a Decision, answered in the convert notebook's decisions cell. The other way in is
Copilot: it writes the same Hive from the workbook's text, and you convert that, as step 11
shows.

## When you'd use it

- If a report lives in an Excel workbook, with its data pasted into Tables, formulas in them,
  a Power Query and a PivotTable, convert the workbook as the steps below do.
- If the PivotTable keeps Excel's default name, such as PivotTable1, answer its name, as step
  7 does: convert proposes one from its sheet, Teams gives teams_pivot.
- If the PivotTable has a slicer, a Report filter or items it hides, decide what the table
  keeps, as step 7 does: the selection as the workbook was last saved, or every value, in one
  table, a Partition each or a table each.
- If you can't run Python, or your team converts with Copilot, have Copilot write the Hive and
  convert it beside the workbook, as step 11 says: the same Decisions and the same Workbook
  check follow.
- If you want more from the table later than the PivotTable showed, such as each team's share
  of a job's hours, change the table's logic in its Table notebook, as Copilot file 21, which
  grows a converted PivotTable, says, with files 03, 05 and 06: never the workbook, which is a
  one-time way in. To weigh a Pivot filter's answers at scale, Copilot file 22, with files 06
  and 17, says how many tables each makes.
- If you have no Project yet, do [Start a Project](#start_a_project) first, and if you haven't
  converted Hive before, read [Convert someone else's Hive](#convert_someone_elses_hive): this
  page takes the same Workflow's steps, from a workbook.

## Steps

### 1. Start from the Starter Example project

Goal: a Project to convert into. Work in your own Project, at its top. This page uses a copy
of the Starter Example project, which the download's Example projects page shows file by file,
made in the folder the page runs in by `example_project("starter")`, a line you leave out in
your own Project. The Intermediate Example project holds this page's batch converted and
finished already, which the same page shows. The Starter's Dev Database, DEV's "database" in
admin/databases.py, is mart. Fill in DEV's "location_root", the folder its tables' files go
under, as [Set your Database settings](#set_your_database_settings) shows, so each table's
folder is placed for you and is no Decision; this page stands in for your edit:

>>> from pathlib import Path
>>> example_project("starter")
>>> from sqlglot_composer import project, run_execute, run_query, show_hive
>>> from warehouse import connect, execute, query
>>> connect(conn)
>>> databases = Path("admin/databases.py")
>>> _ = databases.write_text(databases.read_text(encoding="utf-8").replace(
...     '"<DEV_LOCATION_ROOT>"', '"/data/dev"'), encoding="utf-8")

Done when `connect(conn)` runs without an error. Then step 2.

### 2. Add the Table references of the tables the workbook samples

Goal: a Table reference, with its Key, for each warehouse table the workbook's rows were
pasted from: ops.job_events and ops.job_owners. Convert reads each table through its Table
reference, and a join it can check needs each table's Key, the columns whose values name one
row. The references Workflow, admin/workflows/references/references.ipynb, makes them, as
[Add your tables' references](#add_your_tables_references) shows; this page runs its two
calls, the second accepting each Key it proposes:

>>> print(project.add_references(["ops.job_events", "ops.job_owners"], query=query))
Wrote references/ops__job_events.py and references/ops__job_owners.py: fill in their TODO lines.
ops.job_events: its Key proposed, (event_id), checked with check_key:
  ops.job_events: the key (event_id) holds where job_events.dt IN ('2026-09-23', '2026-09-24').
ops.job_owners: its Key proposed, (job_id, dt), checked with check_key:
  ops.job_owners: the key (job_id) repeats where job_owners.dt IN ('2026-09-23', '2026-09-24'). Keys with more than one row:
   job_id  copies
        1       2
        2       2
        3       2
        4       2
  ops.job_owners: the key (job_id, dt) holds where job_owners.dt IN ('2026-09-23', '2026-09-24').
To accept every proposed Key, write in the decisions cell: "all_tables": {"key": "proposed"}
Wrote references/ops.py: from references import ops gives ops.job_events, ops.job_owners, ops.job_runs, ops.jobs and ops.run_alerts.
Restart the kernel of a notebook that imported references, to see a table added since.
>>> print(project.write_decisions({"all_tables": {"key": "proposed"}},
...                               tables=["ops.job_events", "ops.job_owners"]))
Wrote 1 answer into references/ops__job_events.py.
Each Decision of ops.job_events is made.
Wrote 1 answer into references/ops__job_owners.py.
Each Decision of ops.job_owners is made.
all_tables: key "proposed": accepted the proposed Key of ops.job_events and ops.job_owners, each written as if typed.

Done when references/ holds ops__job_events.py and ops__job_owners.py, each Key accepted. Then
step 3.

### 3. Save the workbook

Goal: the workbook where the convert Workflow reads it. Save it as it is, an .xlsx file beside
the convert Workflow's notebook, in admin/workflows/convert/: convert reads it where it is,
never copied. Here `example_workbook("job_hours.xlsx")` saves a copy of the Intermediate
Example project's, a line of this page alone, as `example_project` is:

>>> example_workbook("job_hours.xlsx")

It holds what a workbook of yours may hold, each on a sheet of its own:

- a Table, job_events, of ops.job_events' rows pasted in, with a formula column,
  `hours = [@minutes]/60`;
- a Table, job_owners, of ops.job_owners' rows: the team that owned each job each day;
- a Power Query, run_hours, typed on its Power Query sheet, which keeps each run's finish
  event, joins it to job_owners on job_id and dt for its team, and loads its rows into a
  Table, run_hours;
- a PivotTable over run_hours on the Teams sheet, keeping Excel's default name, PivotTable1:
  the Sum of hours of each job, with a slicer on team, the data team selected.

Each formula is in a Table, never in loose cells: a formula outside a Table is refused, as the
workbook's rows are only a sample of the warehouse's. The Example projects page shows the
workbook as text, as copilot/workbook_text.py writes it.

Done when admin/workflows/convert/job_hours.xlsx is there. Then step 4.

### 4. Convert it

Goal: a Saved table for each final of the workbook. Open admin/workflows/convert/convert.ipynb
and fill in its names cell: the batch's name as NAME, `"job_hours"`, the workbook as FILES,
`["job_hours.xlsx"]`, and DATABASE, `"ops"`, the database of the tables the workbook samples.
A workbook is named in FILES by its path: FILES left [] reads only the .hql files beside the
notebook. Save the cell, and run "Run up to your Decisions", which runs this call from the
notebook's folder, then stops at the Decisions. Here is its report, up to its next step:

>>> import os
>>> os.chdir("admin/workflows/convert")  # where the notebook runs: this page stands in
>>> said = repr(project.convert("job_hours", files=["job_hours.xlsx"], query=query,
...                             database="ops"))
>>> os.chdir("../../..")  # back to the Project's folder, where the rest of this page runs
>>> print(said.split("\\nNext:")[0])
Converted job_hours: 1 final of job_hours.xlsx, 1 statement, into 1 Saved table in mart: mart.teams_pivot.
Named as proposed, a Decision of each in its checklist: mart.teams_pivot, for PivotTable1 of job_hours.xlsx. Answer "name" in the decisions cell: "proposed" keeps it, or a name of your own renames the table.
Kept each Pivot filter as converted, so each of these tables holds only the rows the PivotTable's filter or slicer selected when the workbook was last saved: mart.teams_pivot, where the slicer on team keeps data. Each is a Decision of its table, which can keep every value instead: answer "pivot_filters" in the decisions cell, as each table's checklist says, with how many tables each answer makes.
admin/workflows/convert/job_hours/batch.md lists each statement, in the order they run, and what it became.
The Workbook check of job_hours.xlsx ran the Hive of each table the workbook gave, on this computer, over the workbook's own Tables, and compared its rows with the values the workbook shows, as last saved. A difference means the Hive doesn't give what the workbook's formula, query or PivotTable gave on the same rows: look at each one, though none stops anything. The workbook's rows are an old sample, so the warehouse's rows will differ from them: this compares the Hive with the workbook alone, never with the warehouse.
mart.teams_pivot, from PivotTable "PivotTable1": every cell matches the workbook, 2 cells compared.

The workbook's one final is the PivotTable: the formula Table and the query are steps of it,
each read by the next piece, so neither is a table of its own. A PivotTable becomes one table
of its rows, at its finest grain: each Row and Column field a column, and each value a column.
Its Grand Totals and subtotals, which Excel shows by default, are not converted: each is
named in the table's checklist with the GROUP BY that gives it from the table's rows. This
workbook's PivotTable has its Grand Total turned off, so it has none to name.
The "Next:" after the report names the steps to come, and the DECISIONS to paste, which step
7 fills in.

Done when the report starts `Converted job_hours:`. Then step 5.

### 5. Read the Hive and the Workbook check

Goal: know what the workbook became, and whether its Hive gives what the workbook shows. The
batch keeps each final's Hive in admin/workflows/convert/job_hours/scripts/, as convert wrote
it from the workbook, and converts it as any script's Hive. Each piece is a CTE, a named query
read by the next: the formula is `minutes / 60 AS hours`, the Power Query a WHERE and a LEFT
JOIN, and the PivotTable a GROUP BY of its Row field, job_id, with its slicer's selection a
WHERE, marked as a Pivot filter:

>>> print(Path("admin/workflows/convert/job_hours/scripts/teams_pivot.hql").read_text(
...     encoding="utf-8"))
WITH job_events AS (
  SELECT
    job_id,
    event_type,
    dt,
    minutes / 60 AS hours
  FROM ops.job_events
), run_hours AS (
  SELECT
    e.job_id,
    o.team,
    e.hours
  FROM job_events AS e
  LEFT JOIN ops.job_owners AS o
    ON e.job_id = o.job_id AND e.dt = o.dt
  WHERE
    e.event_type = 'finish'
)
SELECT
  job_id,
  SUM(hours) AS sum_of_hours
FROM run_hours
WHERE
  (
    team = 'data'
  ) /* Pivot filter: slicer team */
GROUP BY
  job_id;
<BLANKLINE>

The Workbook check, at the end of convert's report and in batch.md, ran that Hive on this
computer, over the workbook's own Tables standing in for ops.job_events and ops.job_owners,
and compared each cell of the PivotTable with the row the Hive gave for it. It never reads the
warehouse: the workbook's rows are an old sample, and the warehouse's will differ:

>>> batch = Path("admin/workflows/convert/job_hours/batch.md").read_text(encoding="utf-8")
>>> print(batch.split("## The Workbook check")[1].split("## Each statement")[0].strip())
of job_hours.xlsx
<BLANKLINE>
It ran the Hive of each table the workbook gave, on this computer, over the workbook's own Tables, and compared its rows with the values the workbook shows, as last saved. A difference means the Hive doesn't give what the workbook's formula, query or PivotTable gave on the same rows: look at each one, though none stops anything. The workbook's rows are an old sample, so the warehouse's rows will differ from them: this compares the Hive with the workbook alone, never with the warehouse.
<BLANKLINE>
- mart.teams_pivot, from PivotTable "PivotTable1": every cell matches the workbook, 2 cells compared.

The 2 cells are the PivotTable's two jobs. A difference would be a line of its own under the
table, such as `job_id 3: Excel 1.18, Hive 1.15`, to look at, though none stops anything. A
cell where the workbook shows an Excel error, such as #REF!, and the Hive gives NULL, is listed
apart, neither a match nor a difference; a piece the check can't run on this computer is
named, with how to compare it by hand.

Done when the Workbook check says every cell matches. Then step 6.

### 6. Read the table's open Decisions

Goal: know what only you can decide. mart.teams_pivot has two Decisions: its name, proposed
from its sheet, as PivotTable1 is Excel's default, and its Pivot filter, the slicer on team.
Its folder is placed under DEV's "location_root", so it is no Decision. project.check() names each, with each answer of the
Pivot filter and how many tables each makes:

>>> said = repr(project.check())  # -> str
>>> for line in said.splitlines():
...     if line.strip().startswith("mart.teams_pivot:"):
...         print(line.strip())
mart.teams_pivot: name: teams_pivot, proposed for PivotTable1 of job_hours.xlsx: keep it with "proposed", or answer a name of your own, which renames the table
mart.teams_pivot: pivot_filters: team, a Pivot filter. The slicer on team keeps data. "keep": 1 table, that selection; "fold": 1 table, every team; "batch": 1 table, a Partition per team; "tables": at least 2 tables, one per team the PivotTable's cache held (data and finance). Answer "keep" to keep its selection as converted, or "fold", "batch" or "tables" to keep every value instead, as its checklist says

Its checklist, tables/mart__teams_pivot/conversion/checklist.md, says what the table shows,
what each answer makes of it, in Excel's words where Excel has them, and which to pick:

>>> checklist = Path("tables/mart__teams_pivot/conversion/checklist.md").read_text(
...     encoding="utf-8")
>>> print(next(line for line in checklist.splitlines() if "Which to pick" in line))
- Pivot filter team, a Decision. What mart.teams_pivot shows: sum_of_hours by job_id, only where the slicer on team keeps data, as the workbook was last saved. Its answers, each given as "pivot_filters": {"team": ...}: "keep", proposed: 1 table, that selection alone. "fold": like dragging team from Filters to Rows in the PivotTable: 1 table, every team, team a column of mart.teams_pivot and part of what one row is, a row for each job_id and team. "batch": 1 table written one team at a time, each run writing its own team's rows: mart.teams_pivot is partitioned on team, a Partition per team (at least 2 Partitions), and the team each run writes is the Script tag TEAM, answered under "tags" with the Run value proposed there. "tables": like Excel's Show Report Filter Pages: a table per team, named mart.teams_pivot_<value>, such as mart.teams_pivot_data: team: at least 2 tables (data and finance). A layer is each field the table is filtered on, and "at least" as these are the values the PivotTable's cache held when the workbook was saved: the warehouse may hold more. Which to pick: to tab through each team in a presentation, as with a slicer, "fold" keeps every team in one table to slice later; "batch" when each team is written on its own schedule; "tables" only for a handful; "keep" when one selection is all anyone needs. A handful of tables, such as 3, is manageable; a hundred is a reason to "fold" or "batch" instead.

Done when you know the two Decisions. Then step 7.

### 7. Answer each Decision in the decisions cell

Goal: an answer for each open Decision. "Run up to your Decisions" printed a whole DECISIONS
to paste into the decisions cell, directly under it. This page stands in for the cell, filled
in:

>>> DECISIONS = {
...     "mart.teams_pivot": {"name": "job_hours", "pivot_filters": {"team": "fold"}},
... }

Each answer, by its kind:

- "name": a name of your own, "job_hours", renames the table, mart.job_hours, its Table
  folder, its Table reference and its placed folder, /data/dev/mart.db/job_hours, with it;
  "proposed" keeps teams_pivot.
- "pivot_filters": the slicer keeps the data team. "keep", proposed, keeps that selection
  alone. "fold" is like dragging team from Filters to Rows in the PivotTable: one table, a row
  for each job and team, every team in it. "batch" writes one team at a time, each into a
  Partition of its own. "tables" makes a table per team, as Excel's Show Report Filter Pages
  makes a sheet per item. Here, to tab through each team in a presentation, as with the
  slicer, "fold" keeps every team in one table, to slice later, as the checklist's "Which to
  pick" says. A handful of tables, such as 3, is manageable; a hundred is a reason to "fold" or
  "batch" instead.

Done when DECISIONS holds the name and the Pivot filter's answer. Then step 8.

### 8. Write each answer in

Goal: each Decision made in the table's files. Run "Run the rest", under the decisions cell:
its first step writes each answer into the Table reference, renames the table, and writes its
logic again for the Pivot filter's answer, from the Hive it was converted from. The files of
mart.teams_pivot go to admin/removed/. This page runs the step's own cell:

>>> print(project.write_decisions(DECISIONS, tables=project.batch_tables("job_hours")))
Wrote 2 answers into references/mart__teams_pivot.py.
mart.teams_pivot: 2 TODO lines left in references/mart__teams_pivot.py, which wait on nothing: fill each in when you like.
  line 1: mart.teams_pivot - TODO: say in one line what one row is.
  line 12: does_not_add_up=[],  # TODO: columns that are averages, ratios or distinct counts
Renamed mart.teams_pivot to mart.job_hours: its Table folder is tables/mart__job_hours/ now, its Table reference references/mart__job_hours.py, and its batch names it so.
mart.job_hours: wrote its logic, its Table reference and its conversion/ Hive again for its Pivot filters' answers: every team, team part of what one row is.
Each Decision of mart.job_hours is made.

The rename places the table's folder again, for its new name:

>>> reference = Path("references/mart__job_hours.py").read_text(encoding="utf-8")
>>> print(next(line.strip() for line in reference.splitlines() if "location=" in line))
location="/data/dev/mart.db/job_hours",  # under its Database's location_root, in admin/databases.py

Done when it says `Each Decision of mart.job_hours is made.` Then step 9.

### 9. See what the table holds now

Goal: the rows the table writes, checked before anything is written. Folded, the slicer's
WHERE is gone and team is part of what one row is: a row for each job and team, the finance
team's too. Its proposed Key is now job_id and team, marked # proposed in its Table reference,
which blocks nothing. Run its notebook's preview(), here on the Example database:

>>> text = show_hive(project.load("mart.job_hours").preview())  # -> str
WITH job_events AS (
  SELECT
    job_events.job_id,
    job_events.event_type,
    job_events.dt,
    job_events.minutes / 60 AS hours
  FROM ops.job_events AS job_events
), run_hours AS (
  SELECT
    e.job_id,
    o.team,
    e.hours
  FROM job_events AS e
  LEFT JOIN ops.job_owners AS o
    ON e.job_id = o.job_id AND e.dt = o.dt
  WHERE
    e.event_type = 'finish'
)
SELECT
  run_hours.job_id,
  run_hours.team,
  SUM(run_hours.hours) AS sum_of_hours
FROM run_hours
GROUP BY
  run_hours.job_id,
  run_hours.team;
>>> run_query(project.load("mart.job_hours").preview(), query)
   job_id     team  sum_of_hours
0       1     data      2.950000
1       2  finance      2.816667
2       3     data      1.183333
3       3  finance      0.550000

The PivotTable's two cells, job 1's 2.95 hours and job 3's 1.183333, are the data team's rows.
Job 3, report_build, moved from data to finance on 2026-09-18, so it has a row for each team.
A reader who wants the data team's alone, as the slicer showed it, reads the table with a
WHERE on team.

Done when the preview gives a row for each job and team. Then step 10.

### 10. Create, write and compare it in dev

Goal: mart.job_hours made and written in your Dev Database, and compared with its query. The
notebook's next steps are calls to the warehouse, yours to run, each a cell of the notebook:
create each table, write each, and compare each with its original, which for a workbook's
table is its query, the rows its Hive gives. Here execute is the Example database's, which
prints the first line of each Hive it is given and changes nothing:

>>> for table in project.batch_tables("job_hours"):
...     run_execute(project.load(table).create(), execute)
execute: CREATE EXTERNAL TABLE IF NOT EXISTS mart.job_hours (
>>> print(project.run_tables(tables=project.batch_tables("job_hours"), execute=execute))
execute: WITH job_events AS (
1 of 1: mart.job_hours  worked
Wrote 1 table, in order.
>>> print(project.compare_batch("job_hours", query=query, partitions=[]))
mart.job_hours: failed, couldn't compare: The Example database couldn't run this Hive: it has no table mart.job_hours.

The Example database holds no Dev Database, so the compare couldn't read the dev table; at
work, once it passes, the batch is finished, and the promote Workflow carries the table to
your Prod Database, as [Convert someone else's Hive](#convert_someone_elses_hive) shows.

Done when the compare says it passed, at work. Then step 11.

### 11. Or have Copilot write the Hive

Goal: the same table from the Hive Copilot writes, for whoever converts a workbook with
Copilot. At work, and nothing on this page runs it:

1. Write the workbook as text: in a terminal in the download's top folder, run
   `python copilot/workbook_text.py "admin/workflows/convert/job_hours.xlsx"`, with your
   workbook's path, which writes job_hours.txt beside it: each Table and formula, the Power
   Query's M, the PivotTable, its fields, its slicer and its cells, and the order each piece
   reads the others in.
2. In a new chat, attach `copilot/15_excel_workbook_steps.txt`,
   `copilot/11_excel_formula_workbooks.txt`, `copilot/12_excel_power_query.txt`,
   `copilot/20_excel_pivot_tables.txt`, for a PivotTable, and
   `copilot/24_excel_pivot_filters.txt`, for its slicer, as `copilot/00_start_here.txt`'s Index
   says, then job_hours.txt, and send "Convert this workbook". A workbook with a Total Row or a
   whole-column total takes `copilot/23_excel_totals.txt` too.
   Copilot answers with a map of the workbook and a Hive query for each final, its slicer's
   condition under `-- Pivot filter: slicer team`, the mark convert reads.
3. Save the query beside the workbook, named for its table, as job_hours.hql, and convert it
   into the same batch, the workbook beside it, `FILES = ["job_hours.xlsx", "job_hours.hql"]`:

       project.convert("job_hours", files=["job_hours.xlsx", "job_hours.hql"], query=query,
                       database="ops")

The .hql stands for the PivotTable's final: it is converted in place of the workbook's own
Hive, and convert's report says so. Its mark gives the same Pivot filter Decision, each answer
written in already is kept, and the Workbook check checks Copilot's Hive against the same
cells, saying `job_hours.hql, Copilot's Hive of PivotTable "PivotTable1": every cell matches
the workbook`. A difference there is Copilot's to fix: paste it into the chat.

Done when convert's report, at work, names job_hours.hql as the PivotTable's Hive and the
Workbook check says every cell matches. Then check it worked, below.

## Check it worked

Before you go on, check that:

- the Workbook check in admin/workflows/convert/job_hours/batch.md says every cell matches;
- references/mart__job_hours.py names the table mart.job_hours, its folder under
  /data/dev, and `"team": "fold"` under PIVOT_FILTERS;
- the preview of mart.job_hours gives a row for each job and team;
- at work, its compare in tables/mart__job_hours/conversion/compare.md says "Passed:".

## Common mistakes

### A formula outside a Table

A formula in loose cells reads by position, which no query can, so the conversion refuses it.
Put the data and each formula into an Excel Table, Insert > Table, and convert again.

### Answering "tables" for a field of many values

"tables" makes a table per value the PivotTable's cache held, and the warehouse may hold more:
a slicer over 100 sites makes at least 100 tables. Its checklist says how many each answer
makes. For more than a handful, answer "fold" or "batch".

### Changing the workbook after it is converted

The workbook is a one-time way in. Once its table is in your Project, change the table's logic
in its Table notebook, never the workbook and a convert again: an edit made to the table
would be written over.

### Naming Copilot's .hql for nothing

A .hql named neither for a final's table, job_hours.hql, nor for its name in the workbook,
pivottable1.hql, is a script of its own: it becomes a second table beside the workbook's,
named for the file. Name it for the table it stands for.

## Next

- [Convert someone else's Hive](#convert_someone_elses_hive): the same Workflow from Hive
  scripts, with Script tags, seeds and promotion.
- [Follow a Workflow](#follow_a_workflow): every Workflow's steps, drawn and listed.
"""  # noqa: E501 - the reports a Project action prints, shown whole
