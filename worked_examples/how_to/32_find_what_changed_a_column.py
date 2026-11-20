"""Find what changed a column

For: Intermediate

## Goal

Find why a column's numbers moved when its own Statement didn't change. A column's own logic
is how its own Statement makes it, with the rows that count for it: the WHERE, JOIN ON, GROUP BY
and HAVING on its way. Its Effective logic is that logic followed through every Saved table it
reads, down to the tables the Project doesn't write. So a change up the chain changes its
Effective logic, while its notebook stays the same. The Lineage state,
admin/lineage/lineage_state.csv, records each column's own logic and Effective logic, a row each
time one changes; the Lineage difference shows what changed between two recordings, each column
marked an Own change or an Inherited change, with the chain down to where it came from and when
your table was first written with its new logic.

## When you'd use it

- If a number moved and nothing in its own Table notebook changed, export the Lineage
  difference for its table, as step 5 does: it names the change up the chain.
- If you changed a table, a Table reference or a Building block by hand, record the Lineage
  state, as step 3 does; until you do, `project.check()` says it is behind.
- If you want to know when the new numbers reached your table, read its "First written with
  this logic" line, as step 5 shows. It comes from admin/sent.csv, which keeps each write the
  Toolbox runs from your Project's notebooks, a Scheduled run's among them when it runs from its
  folder in the Project: a scheduler that runs a copy of the notebook elsewhere leaves no row.
- If you want the state itself, to filter in Excel or pandas, open
  admin/lineage/lineage_state.csv: one row per change, never rewritten.

## Steps

### 1. Start from the Intermediate Example project

Goal: a Project whose Saved tables read one another, with its Lineage state recorded. Work in
your own Project, at its top. This page works in a copy of the Intermediate Example project,
which the download's Example projects page shows file by file: `example_project("intermediate")`
makes that copy in the folder the page runs in. It is a line of this page alone, not a Toolbox
name, as `conn` is this page's connection: in your own Project leave it out.

>>> example_project("intermediate")
>>> from sqlglot_composer import export_hive, project, run_execute
>>> from warehouse import connect, execute, query
>>> connect(conn)

Each Project action that changes a table or Table reference has recorded the Lineage state
already, and so has cell 5, `export_hive()`, of each Table notebook. Here mart.job_day_facts
reads ops.job_events, and mart.team_days reads mart.job_day_facts.

Done when the folder you work in holds admin/lineage/lineage_state.csv and admin/lineage.ipynb.
Then step 2.

### 2. Change a Table reference, no notebook

Goal: a change none of the Table notebooks shows. mart.job_day_facts counts a run's minutes on
the event that ends it, which ops.job_events' Table reference names with its Alias
ends_a_run. Your team now counts a retry as the end of a run too: one word in one file, and
neither mart.job_day_facts's notebook nor mart.team_days's changes. An Alias is written into the
Hive of each Statement that uses it, so changing it is an Own change of each column that uses
it, mart.job_day_facts.minutes here, and an Inherited change of each column that reads that
one.

The file `references/ops__job_events.py`, after you edit it:

    \"\"\"ops.job_events - one row per event of a run: start, retry, finish or fail.

    Why: the project's notebooks read the table through this file, so each column they name,
    and the key each join and count relies on, where it has one, is checked as the Statement
    is built.

    project.add_references wrote this file from the table's DESCRIBE, its partition columns,
    if any, among it. Its three TODO lines were then filled in by hand: this docstring's first
    line, the key, and does_not_add_up. ends_a_run counts a retry too since the team said so.
    \"\"\"
    from sqlglot_composer import Table, is_in

    job_events = Table(
        "ops.job_events",
        columns={
            "event_id": "bigint",
            "job_id": "bigint",
            "event_type": "string",
            "minutes": "int",
            "dt": "string",
        },
        partitioned_by=["dt"],
        key=["event_id"],  # filled in by hand
        # filled in by hand: none of the columns is an average, a ratio or a distinct count
        does_not_add_up=[],
        descriptions={
            "event_type": "start / finish / retry / fail",
            "minutes": "minutes since the run started",
        },
    )

    # --- Aliases ------------------------------------------------------------------------------
    # Your own names for this table's columns and conditions, written by hand below.
    # Import one beside the table: from references.ops__job_events import job_events, <alias>
    #
    # A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
    # get back, still call the column by its own name. To rename an output, use AS(...).
    #     <alias> = job_events.event_type
    # A condition Alias names a condition on this table alone, for WHERE or
    # count_rows(where=...). Add what it calls, such as equals, to the import at the top.
    #     <alias> = equals(job_events.event_type, <value>)

    ends_a_run = is_in(job_events.event_type, ["finish", "fail", "retry"])

`project.check()` sees what changed, and says the Lineage state is behind, since nothing
recorded it yet:

>>> print(project.check())
Every Table folder, Table reference, Building block and Scheduled run is registered, and each
    one registered is there.
The Lineage state is behind: 3 columns' logic differs from its last recording, in
    mart.job_day_facts, mart.team_days and weekly_team.week_totals. Record it with
    project.record_lineage_state(), in admin/lineage.ipynb; a Table notebook's cell 5,
    export_hive(), records the whole Project too.
Done: each convert batch below.
  admin/workflows/convert/convert.ipynb, job_hours: every table the batch wrote passed its
    compare, and its folder is admin/workflows/convert/finished/job_hours/.
  admin/workflows/convert/convert.ipynb, team_failures: every table the batch wrote passed its
    compare, and its folder is admin/workflows/convert/finished/team_failures/.

weekly_team.week_totals is the Scheduled run weekly_team's Statement week_totals: the Lineage
state names a run's Statement <run>.<result>, as the run's results name it. The last lines are
about a batch the Example project converted earlier, which needs nothing from you.

Done when `project.check()` names the tables whose logic differs. Then step 3.

### 3. Record the Lineage state

Goal: the change in admin/lineage/lineage_state.csv. Record it from admin/lineage.ipynb's
record cell, which is this call; cell 5 of any Table notebook records the whole Project the
same way:

>>> print(project.record_lineage_state())
Lineage state: 3 columns changed (1 own, 2 inherited): project.export_lineage_difference()
    shows them.

One Own change, mart.job_day_facts.minutes, whose own logic now holds 'retry', and two
Inherited changes, mart.team_days.minutes and weekly_team.week_totals.minutes, whose own logic
is the same. Recording needs no `connect(...)` and never reaches the warehouse: each Run value
stands in for its value, never called.

Done when the line counts the changes, and `project.check()` no longer says the Lineage state
is behind. Then step 4.

### 4. Write the table, as its notebook does

Goal: the new logic in the warehouse. A table's numbers change only when it is written next, as
mart.job_day_facts's write cell writes it, and admin/sent.csv keeps each write:

>>> run_execute(project.load("mart.job_day_facts").write(), execute)
execute: WITH events_per_job AS (

Done when admin/sent.csv's last row names mart.job_day_facts. Then step 5.

### 5. Export the Lineage difference

Goal: where and when mart.team_days changed. `tables=` keeps the page to that table and every
chain that reaches it. Left out, `since=` compares the newest recording with the one before;
give it a time or a commit to see every change since. Give a time after the tables you ask
about were made: a table made since that time shows only as added, its columns' later changes
inside that.

>>> print(project.export_lineage_difference(tables="mart.team_days"))  # doctest: +ELLIPSIS
Wrote admin/lineage/20260925-090000-difference.html and its Markdown twin,
    20260925-090000-difference.md: 2 tables changed, since ..., to the newest, of 2026-09-25
    09:00:00: 2 columns (1 own, 1 inherited).

The line's "since ..." names the recording it starts from, the one before the newest. It
counts 2 tables though `tables=` named one: mart.job_day_facts is on mart.team_days's chain, and
`tables=` keeps every chain that reaches the table you name.

Open the HTML page: each table is a box, one with an Own change in one colour, one with only an
Inherited change in another, and a click on a box opens its columns beside the drawing. Its
Markdown twin, the file the line names, holds the same sections; these lines of it answer the
question:

>>> from pathlib import Path
>>> twin = Path("admin/lineage/20260925-090000-difference.md").read_text(encoding="utf-8")
>>> for line in twin.splitlines():
...     if line.startswith(("## ", "- `", "First written", "Not written")):
...         print(line.lstrip("# "))
`mart.job_day_facts`: own change
First written with this logic: 2026-09-25 09:00:00 (admin/sent.csv).
`mart.team_days`: inherited change only
Not written since the change (admin/sent.csv).
- `mart.team_days.minutes` ← `mart.job_day_facts.minutes`

mart.team_days.minutes changed only through what it reads: its chain runs to
mart.job_day_facts.minutes, whose own logic changed. Each column's section holds its own logic
and its Effective logic before and after, written out down to ops.job_events. mart.team_days
isn't written since, so its numbers change at its next write.

Done when the page names mart.job_day_facts.minutes as the change mart.team_days comes from.
Then check it worked, below.

## Check it worked

Before you go on, check that:

- `project.check()` doesn't say the Lineage state is behind;
- admin/lineage/lineage_state.csv's last rows are step 3's recording: an own row for
  mart.job_day_facts.minutes, and inherited rows naming it in their because column, which
  names, for an Inherited change, each Own change up its chain it comes from;
- the difference page names each changed table, its chain, and when it was first written with
  its new logic.

## Common mistakes

### Reading the table's own Hive

mart.team_days's .hql, its own Hive, is the same before and after, since its own logic didn't
change: its Effective logic did. Read the Lineage difference, not the table's own Hive, to find
a change up the chain.

### Forgetting cell 5 after an edit

A Table notebook's logic, edited and written but not exported with cell 5, `export_hive()`,
leaves the Lineage state behind: the change is recorded only at the next recording, so a
difference dates it then, not when you made it.
`project.check()` catches it: it says the Lineage state is behind, naming the tables. Run cell
5, or `project.record_lineage_state()` in admin/lineage.ipynb.

### Expecting a Scheduled run to record

A Scheduled run records nothing when it runs, since recording is work each run need not do.
Each Project action that changes a table or Table reference, and each Table notebook's cell 5,
records; a run only builds its Statements and runs them.

### Expecting a new day's value to show as a change

A Run value is recorded as its function and what it was given, never the value it gave, so a
write on a new day is no change. A change to the function, or to what it is given, is.

## Next

- [Follow lineage](#follow_lineage): a Statement's Lineage, column by column, within its own
  Statement.
- [Schedule a run](#schedule_a_run): a Scheduled run, whose Statements' columns the Lineage
  state records too.
"""
