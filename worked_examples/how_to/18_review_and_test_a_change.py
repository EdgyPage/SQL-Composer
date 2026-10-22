"""Review and test a change

For: Intermediate

## Goal

Before you change a Building block that several Statements read, see what the change does to
each of them, and check that they give the numbers you meant. Export their Lineage before the
change and after it and compare the two Markdown files line by line; then work the same
answer out a second way, in pandas, from the rows themselves, and compare the two with plain
`assert`s.

## When you'd use it

Before you change a Building block or a Table reference that other Statements rely on, when
you review someone else's change, and before a Statement's numbers are read by other people.
The lines that differ between the two Markdown files are what the change does, Statement by
Statement, whatever the code looked like. The Toolbox's Guards and Warnings catch mistakes of a
known shape, such as a join that repeats rows; only a test catches a Statement that counts the
wrong thing.

It needs [Share Building blocks](#share_building_blocks), [Save a table](#save_a_table) and
[Follow lineage](#follow_lineage).

## Steps

### Start from the Intermediate Example project

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

>>> import difflib
>>> import pandas as pd
>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> from warehouse import query, execute
>>> from references import ops
>>> job_events, job_owners = ops.job_events, ops.job_owners  # -> Table, Table

### The Building block and the Statements that read it

building_blocks/events_per_job.py is a Building block, as [Share Building
blocks](#share_building_blocks) shows: a Derived table of each job's events, runs and minutes
per day. A run's minutes are on the event that ends it, finish or fail. Two notebooks read it:
mart.job_day_facts saves its numbers, and mart.team_days checks a team's day from them.

`project.load` gives a Table notebook's logic, its functions, as `project.run_tables` reads
them. A function of yours builds the two Statements from them, so after you change the
Building block, one call builds them again; `project.load` reads the files as they are at
that moment:

>>> def build_statements(day: str) -> tuple[Statement, Statement]:
...     facts = project.load("mart.job_day_facts")
...     team_days = project.load("mart.team_days")
...     return facts.write(), team_days.team_day_from_job_events(day)
>>> facts_write, team_day = build_statements("2026-09-18")  # -> Statement, Statement
>>> run_query(team_day, query)  # -> DataFrame
      team  events  runs  minutes
0     data       2     1       14
1  finance       4     2       34

### A second answer, in pandas

Before changing anything, check that `team_day` gives the numbers you mean. Fetch the rows
themselves, every column of every event of the day, and each job's team that day, and work
the answer out in pandas, which counts in a way of its own. This is an oracle, an answer you
trust because you can read each step of it:

>>> def rows_of(day: str) -> pd.DataFrame:
...     events = run_query(statement(
...         SELECT(all_columns(job_events)),
...         FROM(job_events),
...         WHERE(equals(job_events.dt, day)),
...     ), query)
...     teams = run_query(statement(
...         SELECT(job_owners.job_id, job_owners.team),
...         FROM(job_owners),
...         WHERE(equals(job_owners.dt, day)),
...     ), query)
...     return events.merge(teams, on="job_id", how="left")
>>> def oracle(rows: pd.DataFrame, ending: list[str]) -> pd.DataFrame:
...     counted = rows.assign(
...         started=rows["event_type"] == "start",
...         ended=rows["minutes"].where(rows["event_type"].isin(ending), 0))
...     return counted.groupby("team", as_index=False).agg(
...         events=("event_id", "count"), runs=("started", "sum"), minutes=("ended", "sum"))
>>> oracle(rows_of("2026-09-18"), ending=["finish", "fail"])  # -> DataFrame
      team  events  runs  minutes
0     data       2     1       14
1  finance       4     2       34

Fetching every row is fine for a test over a day or two; it is what the Statement saves you
from on the whole table.

### Compare the two with assert

`assert` stops with an AssertionError when what follows it is False, and does nothing when it
is True. `same_rows` puts each DataFrame's rows in one order, by `"team"`, and turns them into
a list of plain dicts, which compare with `==` as Python lists do:

>>> def same_rows(result: pd.DataFrame, expected: pd.DataFrame) -> bool:
...     return (result.sort_values("team").to_dict("records")
...             == expected.sort_values("team").to_dict("records"))
>>> def test_team_day(s: Statement, day: str, ending: list[str]) -> None:
...     result = run_query(s, query)
...     expected = oracle(rows_of(day), ending)
...     assert same_rows(result, expected), f"{day}:\\n{result}\\n{expected}"
>>> test_team_day(team_day, "2026-09-18", ending=["finish", "fail"])

It printed nothing, so the `assert` held. Choose the days to hold the awkward cases: here
2026-09-18, when report_build failed, so a run ended without finishing.

### Export the Lineage before the change

Pass both Statements to [`export_lineage`](examples.html#export_lineage), so one Lineage covers
everything the Building block feeds. `to=` gives the files a name you can find again;
otherwise each export gets a new name, from the time it ran:

>>> html_file, markdown_file = export_lineage(facts_write, team_day, to="before.html")  # -> tuple[Path, Path]

The Markdown file holds, for each Statement, every calculated column with the table columns it
comes from and the conditions that decide which rows count, then the copied columns, then the
Keys, then the Hive, as [Follow lineage](#follow_lineage) shows. Open the HTML page in your
browser to see the same drawn.

### Change the Building block

Say a failed run's minutes shouldn't count, only a finished run's: the minutes line of
events_per_job changes, from where=ends_a_run, the Alias of a finish or a fail, to
`where=equals(job_events.event_type, "finish")`, and its docstring and imports with it:

The file `building_blocks/events_per_job.py`, after you change it:

    \"\"\"events_per_job - each job's events, runs and minutes for each dt it reads.

    Why: mart.job_day_facts saves these numbers, and mart.team_days' notebook checks a day from
    them too, and writing them once here means the two always count them the same way.

    A run's minutes are the minutes since it started, on its finish event: a run that failed
    counts no minutes. A day with no run finishing has 0 minutes, not NULL.
    \"\"\"

    from sqlglot_composer import (
        AS, FROM, GROUP_BY, SELECT, WHERE, Table, between, count_rows, derived, equals,
        fill_null, statement, sum_of,
    )
    from references.ops__job_events import job_events


    def events_per_job(first_day: str, last_day: str) -> Table:
        \"\"\"One row per job and dt from first_day to last_day: its events, runs and minutes.

        The day, dt, ops.job_events' partition column, is kept in GROUP_BY, so each day's numbers
        stay apart when first_day and last_day are days apart, and in SELECT, so a Statement that
        reads this can join each row to another table on its day, and a write that reads it fills
        each day's Partition from it.
        \"\"\"
        return derived(
            "events_per_job",
            statement(
                SELECT(
                    job_events.job_id,
                    job_events.dt,
                    AS(count_rows(), "events"),
                    AS(count_rows(where=equals(job_events.event_type, "start")), "runs"),
                    AS(fill_null(sum_of(job_events.minutes, where=equals(job_events.event_type, "finish")), 0), "minutes"),
                ),
                FROM(job_events),
                WHERE(between(job_events.dt, first_day, last_day)),
                GROUP_BY(job_events.job_id, job_events.dt),
            ),
        )

Then build the Statements again, since each holds the Building block as it was when it was
built, and export the Lineage after:

>>> team_day_before = team_day
>>> facts_write, team_day = build_statements("2026-09-18")
>>> html_file, markdown_file = export_lineage(facts_write, team_day, to="after.html")  # -> tuple[Path, Path]

### Compare the two Markdown files

Python's `difflib.ndiff` compares two lists of lines and marks each line that only the first
holds with "- ", and each that only the second holds with "+ ". `changed_lines` prints those
lines, each under the part of the Markdown file it is in: the Statement, from its `##`
heading, then the column or the Hive, from the heading under that. It leaves out the last line
of each file, which says when the file was made, and so differs every time:

>>> def changed_lines(before_file: str, after_file: str) -> None:
...     before = Path(before_file).read_text(encoding="utf-8").splitlines()
...     after = Path(after_file).read_text(encoding="utf-8").splitlines()
...     part = heading = shown = None
...     for line in difflib.ndiff(before, after):
...         text = line[2:]
...         if text.startswith("## "):
...             part, heading = text[3:], None
...         elif text.startswith("###"):
...             heading = text.lstrip("# ")
...         if line.startswith(("- ", "+ ")) and not text.startswith("Made by export_lineage"):
...             where = part if heading is None else f"{part}, {heading}"
...             if where != shown:
...                 print(f"In {where}:")
...                 shown = where
...             print(line[:100])
>>> changed_lines("before.md", "after.md")
In facts_write, `events_per_job in facts_write.minutes`:
- Calculated in **events_per_job in facts_write** as `fill_null(sum_of(job_events.minutes, where=is_
+ Calculated in **events_per_job in facts_write** as `fill_null(sum_of(job_events.minutes, where=equ
- events_per_job in facts_write.minutes = fill_null(sum_of(job_events.minutes, where=is_in(job_event
+ events_per_job in facts_write.minutes = fill_null(sum_of(job_events.minutes, where=equals(job_even
In facts_write, Hive as submitted:
-     COALESCE(
-       SUM(
-         CASE WHEN job_events.event_type IN ('finish', 'fail') THEN job_events.minutes END
+     COALESCE(SUM(CASE WHEN job_events.event_type = 'finish' THEN job_events.minutes END), 0) AS mi
-       ),
-       0
-     ) AS minutes
In team_day, `events_per_job in team_day.minutes`:
- Calculated in **events_per_job in team_day** as `fill_null(sum_of(job_events.minutes, where=is_in(
+ Calculated in **events_per_job in team_day** as `fill_null(sum_of(job_events.minutes, where=equals
- events_per_job in team_day.minutes = fill_null(sum_of(job_events.minutes, where=is_in(job_events.e
+ events_per_job in team_day.minutes = fill_null(sum_of(job_events.minutes, where=equals(job_events.
In team_day, `minutes`:
- └─ events_per_job in team_day.minutes = fill_null(sum_of(job_events.minutes, where=is_in(job_event
+ └─ events_per_job in team_day.minutes = fill_null(sum_of(job_events.minutes, where=equals(job_even
In team_day, Hive as submitted:
-     COALESCE(
-       SUM(
-         CASE WHEN job_events.event_type IN ('finish', 'fail') THEN job_events.minutes END
+     COALESCE(SUM(CASE WHEN job_events.event_type = 'finish' THEN job_events.minutes END), 0) AS mi
-       ),
-       0
-     ) AS minutes

Each line is cut at 100 characters here. Under the minutes column of each Statement's
events_per_job, the calculation changed, so every number added up from it may change, in
both Statements; in each Hive, the minutes' CASE WHEN changed. Nothing else did: no column came
or went, and no column takes its value from anywhere new.

### Test the change

Run the test's comparison again. It fails on 2026-09-18, the day report_build failed: the
oracle still counts a failed run's minutes, and the changed Building block doesn't. The
finance team's minutes fell by 12, the minutes report_build ran before it failed:

>>> result = run_query(team_day, query)
>>> expected = oracle(rows_of("2026-09-18"), ending=["finish", "fail"])
>>> assert same_rows(result, expected), f"2026-09-18:\\n{result}\\n{expected}"
Traceback (most recent call last):
...
AssertionError: 2026-09-18:
      team  events  runs  minutes
0     data       2     1       14
1  finance       4     2       22
      team  events  runs  minutes
0     data       2     1       14
1  finance       4     2       34

That is the change doing what it was meant to, on exactly the day and team it was meant to:
change the oracle to the new meaning, finished runs only, and test it on several days, the
awkward ones among them. `test_team_day` prints nothing when every `assert` holds:

>>> for day in ["2026-09-14", "2026-09-18", "2026-09-24"]:
...     facts_write, team_day = build_statements(day)
...     test_team_day(team_day, day, ending=["finish"])

## Check it worked

The two Markdown files differ, and the after file names the new condition:

>>> 'where=equals(job_events.event_type, "finish")' in Path("after.md").read_text(encoding="utf-8")
True
>>> 'where=equals(job_events.event_type, "finish")' in Path("before.md").read_text(encoding="utf-8")
False

## Common mistakes

### Exporting the Statements built before the change

A Statement holds its Building block as it was when it was built. Change the file, but
export the Statements you already had, and the Lineage after looks just like the one before.
Here `team_day_before` was built before the change, and still counts a failed run's minutes:

>>> "IN ('finish', 'fail')" in to_hive(team_day_before)
True
>>> "IN ('finish', 'fail')" in to_hive(team_day)
False

Build the Statements again after each change, with `build_statements`, then export. A
function you imported yourself from the Building block also stays as it was until you
restart the notebook's kernel: `project.load` reads the files again each time, an import of
your own doesn't.

### Comparing two DataFrames with ==

`==` between two DataFrames compares them cell by cell and gives back a third DataFrame, of
True and False. `assert` can't say whether a whole DataFrame is true, so it stops:

>>> facts_write, team_day = build_statements("2026-09-18")
>>> result = run_query(team_day, query)
>>> expected = oracle(rows_of("2026-09-18"), ending=["finish"])
>>> assert result == expected
Traceback (most recent call last):
...
ValueError: The truth value of a DataFrame is ambiguous...

Compare lists of rows, as `same_rows` does, or use pandas' own `pd.testing.assert_frame_equal`.

### Comparing rows in the order they came back

The Example database gives rows in a fixed order, but your warehouse gives them in no fixed
order. Compare without sorting, and a right answer fails whenever the order differs, as it does
here, with the most minutes first:

>>> most_first = expected.sort_values("minutes", ascending=False)
>>> result.to_dict("records") == most_first.to_dict("records")
False
>>> same_rows(result, most_first)
True

Put both in one order before comparing, as `same_rows` does with `"team"`.

### An oracle that asks the Statement

An oracle built from the Statement's own result always agrees with it, right or wrong. No
message stops you:

>>> same_rows(result, result)
True

Work the oracle out from the rows themselves, as `oracle` does from `rows_of`, and in another
way than the Statement does.

## Next

- [Check data quality](#check_data_quality): checks on the data itself, so a Statement you've
  tested gets rows you can trust.
- [Declare a change made in Python](#declare_a_change_made_in_python): a step whose Lineage is
  one box, naming the function to review.
- The gallery's [`export_lineage`](examples.html#export_lineage) and
  [`derived`](examples.html#derived) entries.
"""
