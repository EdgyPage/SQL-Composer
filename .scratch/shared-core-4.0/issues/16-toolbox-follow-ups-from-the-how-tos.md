# Toolbox follow-ups the how-tos found

Type: task
Status: open
Blocked by: 07, 09, 10
Size: M

## Question

Writing and reviewing the 30 how-tos and two Example projects (tickets 07-12) turned up places
where the Toolbox's own messages or behaviour mislead, outside those tickets' files. The how-tos'
doctests quote refusal text, so this runs after their fix-ups and updates their expected output.

Bugs:
1. `refusals.warn_at_callers_line` passes `module=frame.f_globals.get("__name__")`, None in a scope
   with no `__name__`, and `warnings.warn_explicit` then drops the Warning; under `python -c` the
   `module_globals` it passes crash with "'__main__' is not a built-in module".
2. Lineage: a downstream reader's "Rows that count" lists an upstream writer's conditions (ticket
   12: mart.team_days' columns list owner_on_day's LEFT JOIN ON when `team`, from that LEFT JOIN,
   is the GROUP_BY key; ticket 09: how-to 23's weekly rollup lists the job_owners.dt bound of the
   team_day write). Decide what is right and fix, with tests (ticket 11's fix is the precedent).
3. sqlglot Composer's Example database gives a wrong result (NaN job_id) for LEFT JOIN + GROUP BY
   + count_rows(where=...) over Derived tables (ticket 09). Find it; refuse or fix.
4. A stray RepeatedRowsWarning "matches on nothing" when one Statement reads one block twice
   (ticket 07's review).

Messages:
5. `run` given a non-Statement refuses in `to_hive`'s name ("to_hive was given ..."): refuse in
   run's own name; for a Derived table, say to wrap it: statement(SELECT(all_columns(d)), FROM(d)).
6. A day written the wrong way: "Write the day as '20260925'" uses a fixed example day: say
   "like"; when the text reads under another format (e.g. '20260918' under %Y%m%d), suggest that
   date_format=.
7. HAVING given a calculation's name as text: point at writing the calculation itself.
8. The missing-GROUP_BY refusal suggests the Date partition (job_events.dt) for a week_start
   column, which would group by day.
9. The repeated-rows Warning's fix on a snapshot table: name the missing key part (dt) when the
   joined table's key has it.
10. write_table_reference's FileExistsError names an absolute path: name the file, in the folder
    you're working in (the how-to page can then show it live).
11. write_table_reference's TODO for a table first partitioned by something other than days says
    "its newest region, 'us'": say "its last region value".

New behaviour, the user's answers (2026-10-05): both yes, as recommended.
12. A Guard for `equals` between two Date partitions whose date_format differs (it builds and
    matches nothing; ticket 12). The user chose a Guard: refuse with a four-part message naming
    both formats; no opt-out, since it can never be right.
13. A refusal for a `send` that returns something other than a DataFrame, such as a plain list
    (ticket 06's beginner read). The user chose a clear refusal: `run` stops with a four-part
    message showing how-to 1's `pd.DataFrame(rows)` fix.

## Done when

- Each is fixed with a test, or answered here; the how-tos' and Example projects' expected output
  regenerated; both runs pass; the code review and the beginner reader have run on the messages;
  CHANGES lines go into the map's ticket-15 note.

## Answer, items 5-13

Fixed in 4860c10, with the review fixes in the commit after it. Every test is in the shared
tests, so both Editions run them: tests/test_misuse_refusals.py (5, 7, 13),
tests/test_date_partition_days.py (6), tests/test_refusals.py (8, 9, 12),
tests/test_tables.py (10), tests/test_example_database_intermediate.py and
tests/test_warehouse_answers.py (11).

5. `run`, `to_hive` and `show_hive` refuse what isn't a Statement in their own name
   (running.py, `_need_statement`): "run was given derived('runs_per_job', ...), which isn't a
   Statement." For a Derived table the fix is
   `run(statement(SELECT(all_columns(two_days)), FROM(two_days)), send=...)`, with the caller's
   own variable name, or `d` and "where d is the Derived table" when it has none; for a list,
   `for step in steps: run(step, send=...)`; for Hive text, pass the Statement itself.
   How-tos 4, 8 and 12 show the new What happened; their prose no longer explains to_hive.
6. A day written the wrong way now says "but its Table reference writes days like
   '2026-09-18'": the user's own day, written the table's way, whenever it can be read under
   any of the three usual formats, and "like '2026-09-25' (an example day)" only when it can't
   (then the fix also offers last_n_days). When the text reads under another format, the fix
   adds: "If the table's days really are written like '20260918', add date_format="%Y%m%d" to
   its Table reference instead." How-tos 3, 19 and 26 show it; how-to 19's paragraph about the
   example day is rewritten.
7. A text where a comparison's column goes (equals, not_equals, at_least, at_most, more_than,
   less_than, between) adds: "If "runs" is a name you gave with AS, write the calculation
   itself in its place, as in at_least(count_rows(), ...) for AS(count_rows(), "runs"): WHERE
   and HAVING are worked out before SELECT names anything." is_null and the others don't get
   the hint. How-to 6's prose points at the fix.
8. A calculation in SELECT that GROUP_BY leaves out, such as `AS(week_start(job_events.dt),
   "week")`, is named as itself: "SELECT has the calculation "week" (from job_events.dt), but
   the Statement counts or adds up rows and has no GROUP_BY." The fix is `GROUP_BY("week")`,
   with "A calculation is grouped by the name you gave it with AS.", and neither "put it inside
   a count or a sum" nor the row_number advice. How-to 21's prose is rewritten. Left as it was:
   a calculation in ORDER_BY or HAVING still names its columns (a calculation there has no AS
   name to group by).
9. The repeated-rows Warning on a table whose key holds its Date partition, when ON= leaves it
   out, says: "Match the day too, so each row meets its own day's job_owners row:
   ON=all_of(equals(...), equals(job_owners.dt, job_events.dt)), where equals(...) is what ON=
   has now." The other table is the one ON= already matches with; its day is guessed to have
   the same name. How-to 20's prose points at it. A Derived table has no Date partition, so it
   keeps the usual fix.
10. "job_runs.py already exists in the folder you're working in, so nothing was written."
    How-to 2's Common mistake now runs it live.
11. The TODO says "its last region value, 'us', isn't a day the Toolbox can bound; if dt holds
    the days, name it in date_partition=". How-to 19's prose follows.
12. A new Guard, `guard_date_formats_differ`, no opt-out: any comparison between two columns of
    days written different ways (equals, the other comparisons, between, is_in, and so JOIN's
    ON=) refuses when the value side is a column, checked in `literal`, the one place a value
    enters a Statement. A Derived table's column that passes a Date partition on unchanged is
    followed to it. "equals(region_costs.dt, ...) compares region_costs.dt, whose days are
    written like '20260925' (date_format='%Y%m%d'), with job_events.dt, whose days are written
    like '2026-09-25' (date_format='%Y-%m-%d')." Its fix is to save one table's rows in a Saved
    table written the other's way, pointing at the intermediate Example project's
    statements/example_1_job_day_costs.py. equals' docstring says so; how-to 19 has a new
    Common mistake showing it live; the intermediate Example project's README and example 1's
    docstring no longer say the Toolbox doesn't stop such a join. Not covered: a calculation of
    a Date partition, such as max_of(region_costs.dt), which the Toolbox can't tell is a day.
13. `run` refuses a read whose send gives back anything but a pandas DataFrame (after the
    Spark DataFrame check): "Your send gave back a list, where a pandas DataFrame goes." The
    fix shows `return pd.DataFrame(rows)`, the dict/tuple caveat with
    `pd.DataFrame(rows, columns=names)`, and points at how-to 1; for None it says to end the
    send with return. A write's send may give back anything, as before. How-to 1's sqlglot
    Composer Common mistake runs a list-returning send live.

**Code review (2026-10-05).** Standards: no hard violations (no public name added, parity
holds, everything in composer_core). Judgement calls, fixed: the date-formats fix's "a write
writes its day the Saved table's way" and its unlocated "example 1" (reworded, and it names the
file and the download's example_projects folder); "check_table_reference(t, send=...) says
which" (dropped: the fix says to add the date_format line); the Warning's "the day of the rows
before the join" (now the exact ON=all_of(...)); an "it" with no clear referent in the
DataFrame refusal's why (reworded); "checks it" for a Guard, a word the glossary avoids
(dropped from the messages; the helper is `_guard_days_written_alike`); the GROUP_BY guard
finding a calculation by a quote character (now a list of (name, columns) pairs); the example
day spelled out three times (now `EXAMPLE_DAY` in tables.py); `more` switching on the
caller's name (now a parameter); the string surgery on the Warning's fix (both sentences
written out); the dense zip in `_guard_group_by` (now enumerate). Spec: the item-7 hint fired
for every text in any condition, such as is_null("n") (now only the comparisons); 6's
'2026-9-18' on a %Y%m%d table now shows the user's own day; 8 in ORDER_BY and 12 through
max_of are left as noted above; `to_hive` and `show_hive` gained the same fixes as run, kept
on purpose since a Derived table or list given to them is the same mistake; is_in of two Date
partitions written alike refusing with a ValueError predates this ticket and is left.

**Beginner reader (2026-10-05).** It provoked every message and read the how-tos. Its three
costliest stops, all fixed: the GROUP_BY message naming job_events.dt when SELECT held
week_start(job_events.dt) as "week", and offering a sum of a date (now names the calculation,
offers only GROUP_BY("week")); the date-formats fix asking for a Saved table and a file it
couldn't find (now names the folder and file); the Warning's fix not saying how to put a second
condition in ON= nor which day (now the exact all_of with job_events.dt). Also fixed: the fixed
example day beside the user's own (the message now writes the user's own day, and marks an
example day as one); "check_table_reference(t, ...) says which"; the why and fix of item 7
pulling against each other (the why now names calculations); a Derived table with no variable
name giving a fix that would NameError when pasted (now `d`, "where d is the Derived table");
"yesterday" (the fix offers last_n_days); "result["team"]" (dropped); the TODO's "name it"
(now "name it in date_partition="); "So is ... which no day would pass" in equals' docstring
(reworded). Left: "filters" in write_table_reference's why, which predates this ticket; the
Statement repr's `s`, which predates it; the long Hive repr when run is given Hive text; the
why-not of converting days in the query, since the Toolbox has no function for it; and the
RepeatedRowsWarning crash under `python -c`, which is item 1, another agent's.
