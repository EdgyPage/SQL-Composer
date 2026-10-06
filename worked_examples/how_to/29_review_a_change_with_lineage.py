"""Review a change with Lineage

For: Intermediate

## Goal

Before you change a Building block that several Statements read, see what the change does to
each of them. Export their Lineage before the change and after it, compare the two Markdown
files line by line, and find every output a column feeds.

## When you'd use it

Before you change a Building block or a Table reference that other Statements rely on, and
when you review someone else's change: the lines that differ between the two Markdown files
are what the change does, Statement by Statement, whatever the code looked like.

## Steps

### Import the Toolbox

>>> from sqlglot_composer import *
>>> from pathlib import Path
>>> import difflib
>>> job_events = example_database.job_events
>>> jobs = example_database.jobs

### A Building block and the Statements that read it

`finished_runs` is a Building block, as in [Share Building blocks between
Statements](#share_building_blocks_between_statements): a Derived table of each job's finished
runs over the days you give it, and the minutes they took.

>>> def finished_runs(first_day, last_day):
...     return derived("finished_runs", statement(
...         SELECT(job_events.job_id,
...                AS(count_rows(), "runs"),
...                AS(sum_of(job_events.minutes), "minutes")),
...         FROM(job_events),
...         WHERE(between(job_events.dt, first_day, last_day),
...               equals(job_events.event_type, "finish")),
...         GROUP_BY(job_events.job_id),
...     ))

Two Statements read it: the minutes each team's jobs ran, and the two jobs that ran longest.
A function builds both, so after you change the Building block, one call builds them again:

>>> def build_statements(first_day, last_day):
...     runs = finished_runs(first_day, last_day)
...     minutes_per_team = statement(
...         SELECT(jobs.team, AS(sum_of(runs.minutes), "minutes")),
...         FROM(runs),
...         JOIN(jobs, ON=equals(jobs.job_id, runs.job_id)),
...         GROUP_BY(jobs.team),
...     )
...     longest_jobs = statement(
...         SELECT(jobs.job_name, runs.runs, runs.minutes),
...         FROM(runs),
...         JOIN(jobs, ON=equals(jobs.job_id, runs.job_id)),
...         ORDER_BY(descending(runs.minutes)),
...         LIMIT(2),
...     )
...     return minutes_per_team, longest_jobs
>>> minutes_per_team, longest_jobs = build_statements("2026-09-18", "2026-09-24")
>>> run(minutes_per_team, send=example_database.send)
      team  minutes
0     data       82
1  finance      112

### Export the Lineage before the change

Pass both Statements to [`export_lineage`](examples.html#export_lineage), so one Lineage covers
everything the Building block feeds. `to=` gives the files a name you can find again;
otherwise each export gets a new name, from the time it ran:

>>> html_file, markdown_file = export_lineage(minutes_per_team, longest_jobs,
...                                           to="before.html")

The Markdown file holds, for each Statement, every calculated column with the table columns it
comes from and the conditions that decide which rows count, then the copied columns, then the
Hive, as [Lineage of one Statement](#lineage_of_one_statement) and [Lineage of a pipeline across
Saved tables](#lineage_of_a_pipeline_across_saved_tables) show. Open the HTML page in your
browser to see the same drawn.

### Change the Building block

A run that fails uses the cluster too, so count its minutes as well: the condition becomes
`is_in(job_events.event_type, ["finish", "fail"])`. Keep the function as it was under another
name, for the last mistake below, then write it again with the change, and build the
Statements again, since each holds the Building block as it was when it was built:

>>> finished_only = finished_runs
>>> def finished_runs(first_day, last_day):
...     return derived("finished_runs", statement(
...         SELECT(job_events.job_id,
...                AS(count_rows(), "runs"),
...                AS(sum_of(job_events.minutes), "minutes")),
...         FROM(job_events),
...         WHERE(between(job_events.dt, first_day, last_day),
...               is_in(job_events.event_type, ["finish", "fail"])),
...         GROUP_BY(job_events.job_id),
...     ))
>>> minutes_per_team, longest_jobs = build_statements("2026-09-18", "2026-09-24")
>>> html_file, markdown_file = export_lineage(minutes_per_team, longest_jobs,
...                                           to="after.html")

### Compare the two Markdown files

Python's `difflib.ndiff` compares two lists of lines and marks each line that only the first
holds with "- ", and each that only the second holds with "+ ". `changed_lines` prints those
lines, each under the part of the Markdown file it is in: the Statement, from its `##`
heading, then the column or the Hive, from the heading under that. It leaves out the last line
of each file, which says when the file was made, and so differs every time:

>>> def changed_lines(before_file, after_file):
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
...             print(line)
>>> changed_lines("before.md", "after.md")
In Graph:
-     n6{{"WHERE in finished_runs in minutes_per_team<br/><small>equals(...
...
In longest_jobs, Hive as submitted:
-     AND job_events.event_type = 'finish'
+     AND job_events.event_type IN ('finish', 'fail')

The chart, under Graph, changed its two condition boxes (`#quot;` is Mermaid's way of writing
a quote). Under every calculated column of both Statements, the condition in "Rows that
count" changed, so every number each Statement adds up may change. In each Hive, the WHERE
changed. Nothing else did: no column came or went, and no column takes its value from
anywhere new.

Run the Statements again to see what the change does to the numbers. The finance team's
minutes grew by 12, the minutes report_build ran on 2026-09-18 before it failed:

>>> run(minutes_per_team, send=example_database.send)
      team  minutes
0     data       82
1  finance      124

### Find every output a column feeds

Say the minutes in `ops.job_events` are to be stored as seconds instead. Which outputs would
change? In the Markdown file, each calculated column's part, under its `####` heading, draws
the table columns it comes from as a tree, on lines holding `├─` or `└─`, and each copied
column's row of the Copied columns table says where it is copied from. So search those lines
for the column. `outputs_fed_by` keeps the outputs of the Statements, named like
`minutes_per_team.minutes`, and leaves out the Derived table's own columns, whose headings hold a
dot already, such as `finished_runs in minutes_per_team.minutes`:

>>> def outputs_fed_by(column, markdown_file):
...     fed, statement_name, output = [], None, None
...     for line in Path(markdown_file).read_text(encoding="utf-8").splitlines():
...         if line.startswith("## "):
...             statement_name = line[3:]
...         elif line.startswith("#### "):
...             output = line[5:].strip("`")
...         elif line.startswith("| `"):
...             output = line.split("`")[1]
...         carries_a_value = "─ " in line or line.startswith("| `")
...         if carries_a_value and column in line and "." not in output:
...             name = statement_name + "." + output
...             if name not in fed:
...                 fed.append(name)
...     return fed
>>> outputs_fed_by("ops.job_events.minutes", "after.md")
['minutes_per_team.minutes', 'longest_jobs.minutes']

Both outputs named minutes would come out 60 times bigger. `outputs_fed_by` follows values
only. A column can also decide which rows count, through WHERE, JOIN's ON=, ORDER_BY or LIMIT,
as `ops.job_events.event_type` decides which runs `finished_runs` keeps: that shows under each
calculated column's "Rows that count", which it doesn't search, and not at all under a copied
column. To see every output a column reaches either way, open the HTML page and click the
column's box to light up every path from it.

## Check it worked

The two files differ, and the after file names the new condition:

>>> "event_type IN ('finish', 'fail')" in Path("after.md").read_text(encoding="utf-8")
True
>>> "event_type IN ('finish', 'fail')" in Path("before.md").read_text(encoding="utf-8")
False

## Common mistakes

### Exporting the Statements built before the change

A Statement holds its Building block as it was when it was built. Change the function, but
export the Statements you already had, and the Lineage after looks just like the one before.
Here the change is a step back: the function goes back to finished runs only, kept as
`finished_only`, so the Lineage from before this change is after.md. The Statements aren't
built again:

>>> finished_runs = finished_only
>>> html_file, markdown_file = export_lineage(minutes_per_team, longest_jobs,
...                                           to="stale.html")
>>> changed_lines("after.md", "stale.md")

Nothing printed: no line differs from after.md, though the function changed. Build the
Statements again after each change, with `build_statements`, then export.

### Comparing the HTML pages

The HTML page holds the same Lineage, but as HTML and data for its drawing, on very long lines,
so a line by line comparison of two pages shows little you can read. The lines that differ
between before.html and after.html, by their length in characters:

>>> before_page = Path("before.html").read_text(encoding="utf-8").splitlines()
>>> after_page = Path("after.html").read_text(encoding="utf-8").splitlines()
>>> sorted(len(line) for line in difflib.ndiff(before_page, after_page)
...        if line.startswith(("- ", "+ ")))
[52, 52, 73, 73, 88, 89, 662, 663, 671, 702, 703, 711, 888, 928, 5862, 5906]

Sixteen lines, most of them hundreds of characters long, the last two thousands. Compare the
Markdown files, which `export_lineage` writes beside each page with the same name,
ending in .md.

## Next

- [Generate Table references and Statements from settings](#generate_from_settings): one
  Lineage for Statements generated over many tables.
- [Test your own Statements](#test_your_own_statements): check the numbers a change gives,
  against pandas, before and after it.
- The gallery's [`export_lineage`](examples.html#export_lineage) and
  [`derived`](examples.html#derived) entries.
"""
