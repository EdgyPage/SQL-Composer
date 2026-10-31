"""Convert someone else's Hive

For: Intermediate

## Goal

Turn a long query of Hive someone else wrote, with its CTEs, its lists pasted in by hand and its
if/else chains, into your own code: a Table notebook whose logic builds the same query from the
Toolbox's functions, checked against the original, then saved as a table of your own. That is a
Conversion. What no Toolbox function writes yet stays Hive, at the smallest size it can, so you
get the rest converted rather than none of it.

## When you'd use it

When you inherit Hive that works but that you can't maintain: a report another team wrote, a
query copied from a dashboard, a script that has grown for years. Converted, its lists are named
constants at the top, each CTE is a Derived table, the Guards check it, and Lineage traces it.

It needs [Start a Project](#start_a_project) and [Save a table](#save_a_table).

## Steps

### Start from the Intermediate Example project

Work in a copy of the Intermediate Example project, at its top, as
[Reconcile two tables](#reconcile_two_tables) does. This page makes the copy in its first step:

>>> import shutil
>>> from pathlib import Path
>>> import sqlglot_composer
>>> download = Path(sqlglot_composer.__file__).parents[1]  # -> Path
>>> _ = shutil.copytree(download / "example_projects" / "intermediate", ".", dirs_exist_ok=True)
>>> from sqlglot_composer import compare_with_original, project, to_hive
>>> from warehouse import query

### Paste the Hive in

Open admin/convert.ipynb, which `project.start()` wrote, and paste the Hive between the triple
quotes of its `HIVE` cell. Set DATABASE there too: a table the Hive names without its
database, such as job_events, is taken to be in it. This Hive names each table's database,
so the calls below leave database= out.

Here it is a weekly report of the kind you inherit: SET lines, two CTEs,
a list of event types, a lookup of team names, an if/else chain, a whole-number division, and
an INSERT into the other team's table:

>>> HIVE = '''SET hive.exec.parallel=true;
... -- Weekly event report, as the ops team wrote it
... WITH ev AS (
...   SELECT e.job_id, e.dt, e.event_type, e.minutes
...   FROM ops.job_events e
...   WHERE e.dt BETWEEN '2026-09-20' AND '2026-09-24'
...     AND e.event_type IN ('start', 'retry', 'fail', 'timeout')
... ), per_job AS (
...   SELECT ev.job_id, ev.dt,
...          SUM(CASE WHEN ev.event_type = 'fail' THEN 1 ELSE 0 END) AS fails,
...          SUM(ev.minutes) AS minutes
...   FROM ev
...   GROUP BY ev.job_id, ev.dt
... )
... INSERT OVERWRITE TABLE ops_reports.weekly_events PARTITION (dt)
... SELECT o.team,
...        CASE o.team WHEN 'data' THEN 'Data platform' WHEN 'web' THEN 'Web' ELSE 'Other' END AS team_name,
...        p.job_id,
...        p.fails,
...        CASE WHEN p.minutes > 120 THEN 'heavy' WHEN p.fails > 0 THEN 'failing' ELSE 'light' END AS load,
...        p.minutes DIV 60 AS hours,
...        upper(o.owner) AS owner,
...        p.dt
... FROM per_job p
... JOIN ops.job_owners o ON o.job_id = p.job_id AND o.dt = p.dt
... '''

Hive kept in a file works the same way: pass `file="weekly.hql"`, its path from the folder
you're working in, in place of the text.

### Scan it

`project.scan_hive` reads the Hive and says what a Conversion of it would make, line by line,
and changes nothing:

>>> print(project.scan_hive(HIVE))
25 lines of Hive, one query reading ops.job_events and ops.job_owners.
Found:
  line 1: its SET line is the Session settings HIVE_SETTINGS, which session_settings() gives
  line 7: the IN list of 4 values is the constant EVENT_TYPE_VALUES
  line 15: its INSERT OVERWRITE ops_reports.weekly_events PARTITION(dt) becomes your own Saved
      table's write, INSERT_OVERWRITE(...), with the same partitions
  line 17: the CASE on o.team is the constant TEAM_NAME_BY_TEAM
  line 20: the CASE WHEN chain of 2 conditions becomes first_match(...), which tries them in
      order, as CASE does
  line 21: p.minutes DIV 60 stays Hive, in unchecked_column(...): no Toolbox function writes it
      yet
  line 22: upper(...) is a Hive function no Toolbox function wraps: hive_function("upper", ...)
      writes it

Both tables have Table references in this Project already. One that has none is listed by the
scan, under "No Table reference yet", and the next step adds it, through your query.

Its SET line becomes HIVE_SETTINGS, a dict of the settings by the name of the step they go
before, here "converted", and session_settings() in the logic gives them as Session settings.
Send those with run_execute before the table's write(), as the original sent its SET lines
first: write() sends only the query.

### Convert it

Give the Conversion a name of its own, a plain lowercase one: the Saved table's name is yours
to choose when you finish it.

>>> print(project.convert("weekly_events", HIVE, query=query))
Converted weekly_events: 25 lines of Hive into
    admin/conversions/weekly_events/weekly_events.ipynb.
1 piece kept as Hive, 3 named constants, 1 opt-out marked # CONVERSION: for you to check:
    JOIN(o, reads_all_partitions=True).
Its Hive and the original's: The Statement's Hive and the original are the same query, once both
    are written out the same way.
admin/conversions/weekly_events/scan.md lists what it found, line by line.

Open admin/conversions/weekly_events/weekly_events.ipynb. Its logic cell holds your code: the
list and the lookup as constants at the top, each CTE a Derived table, and rows(), the clauses
of the query, which converted() builds. `project.load` runs that cell from anywhere in the
Project, as it does a Table notebook's:

>>> logic = project.load("weekly_events")  # -> TableLogic
>>> print(to_hive(logic.converted()).splitlines()[0])
WITH ev AS (

### Decide each mark

The original joins ops.job_owners on its partition column, dt, matched with the other table's,
which the Load limit can't tell bounds it, so the Conversion added the opt-out the original's
join needs, reads_all_partitions=True on that JOIN, with a mark on the line above it:
"# CONVERSION: reads_all_partitions=True, as the original did; check it". `project.check()`
lists each mark left:

>>> print(project.check())
Conversions not finished yet: finish each with project.finish_conversion(...), or archive it
    with project.remove_conversion(...):
  admin/conversions/weekly_events/
Marked by project.convert(...) for you to check: decide each opt-out the original took: keep it,
    or change what made it needed, such as a WHERE on the partition column or a key= in a Table
    reference, and take it off; then delete its mark.
  admin/conversions/weekly_events/weekly_events.ipynb, cell 3, line ...: # CONVERSION:
      reads_all_partitions=True, as the original did; check it

An opt-out is a keyword that tells a Guard or a Load limit you have checked what it refuses.
Here the other table holds five days only, so the join reads only those: keep the opt-out, and
delete the mark. At work, ask how many Partitions the join reads: if it reads too many, add a
WHERE on o.dt to bound it, and take the opt-out off.

### Compare it with the original

The notebook's cells compare the two: their Hive, always, and their rows, through your query,
on one Partition:

>>> print(compare_with_original(logic.converted(), HIVE, query=query,
...                             partition={"dt": "2026-09-24"}))
The Statement and the original give the same rows where dt = '2026-09-24': 2 rows each.
The Statement holds Hive written by hand, which the Toolbox can't look inside:
    unchecked_column("{minutes} DIV 60", minutes=p.minutes). The rows match, so it gives what
    the original gives here.

### Finish it

When it gives the rows you want, finish it under the name of a Saved table of yours:

>>> print(project.finish_conversion("weekly_events", table="mart.weekly_events"))
Finished the Conversion weekly_events as mart.weekly_events:
    tables/mart__weekly_events/mart__weekly_events.ipynb, and its Table reference,
    references/mart__weekly_events.py.
Fill in references/mart__weekly_events.py: its <LOCATION>, any <COLUMN_TYPE>, key=, and its TODO
    lines; then run the notebook's create() and write().
The Conversion folder is archived, kept as it was, in admin/removed/...-weekly_events/.

Its Table reference lists the columns the query gives, the types the Toolbox knows, and
`partitioned_by=["dt"]`, from the original's PARTITION(...). Fill in the rest: each
<COLUMN_TYPE> is a column whose type the Toolbox can't tell, such as a CASE's, so write the Hive
type it holds, as DESCRIBE of the other team's table shows.

The file `references/mart__weekly_events.py`, after you fill it in:

    \"\"\"mart.weekly_events - one row per job and day: its events, fails and load.\"\"\"

    from sqlglot_composer import Table

    weekly_events = Table(
        "mart.weekly_events",
        columns={
            "team": "string",
            "team_name": "string",
            "job_id": "bigint",
            "fails": "bigint",
            "load": "string",
            "hours": "int",
            "owner": "string",
            "dt": "string",
        },
        partitioned_by=["dt"],
        key=["job_id", "dt"],
        location="/data/mart.db/weekly_events",
    )

Its notebook's write() writes the table as the original's INSERT did. It keeps the original's
days, as written: to write the last few days on each run, make them a Building block, as the
Intermediate Example project's days_rewritten.py does. Its INSERT line:

>>> table = project.load("mart.weekly_events")  # -> TableLogic
>>> [line for line in to_hive(table.write()).splitlines() if line.startswith("INSERT")]
['INSERT OVERWRITE TABLE mart.weekly_events PARTITION(dt)']

## Check it worked

`compare_with_original` says the two give the same rows on a Partition you choose, and
`project.check()` lists no `# CONVERSION:` mark and no Conversion not finished.

## Common mistakes

- **Converting a script.** A Conversion reads one query. A script of several, SET lines aside,
  is refused: save each query in a file of its own and convert each.
- **Leaving the marks.** A `# CONVERSION:` mark is a chance the original took, such as a join
  that may repeat rows. Decide each: keep the opt-out, or fix the query, then delete the mark.
- **Trusting the Hive alone.** Two queries can differ in their Hive and give the same rows, or
  the other way round where a piece stayed Hive: compare their rows too.

## Next

- [Hand-written Hive with your Table references](#hand_written_hive_with_your_table_references):
  the Unchecked pieces a Conversion leaves, and how to replace them.
- [Upgrade your Project to a new Toolbox
  version](#upgrade_your_project_to_a_new_toolbox_version).
- The gallery's [`compare_with_original`](examples.html#compare_with_original) entry.
"""  # noqa: E501 - the Hive it converts, whose line numbers its output reports
