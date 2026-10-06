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

## Answer, items 1-4

1. **The Warning in a scope with no `__name__`, and under `python -c`.** `warn_explicit` drops a
   Warning whose `module` is None, and given `module_globals` it asks the loader for the
   source, which `__main__`'s BuiltinImporter refuses under `python -c`. `warn_at_callers_line`
   now names the module as `warnings.warn` does (`"<string>"` when the scope has no
   `__name__`) and passes no `module_globals`, as `warnings.warn` passes none. Tests: a JOIN
   in `exec` with no `__name__` warns; a JOIN under `python -c` prints the Warning and goes on.
   how_to_page.py's comment that Python drops such a Warning is gone.
2. **Lineage: an upstream writer's conditions under a reader's "Rows that count".** The walk
   reached a LEFT_JOIN's ON= from every column of its Statement, since each condition has a
   "rows" arrow to every output, and from there every reader of the Saved table it writes.
   Decided, following ticket 11's reason (a LEFT_JOIN keeps every row before it, once each):
   a LEFT_JOIN's ON= (many_matches=False) decides only the columns read from its table, so
   `_deciding` passes from a column to it only when the column reads that table, or when
   another condition of the same step that can drop rows reads it (an anti-join's
   WHERE(is_null(...)), which keeps the rows the ON= didn't match), or a second LEFT_JOIN
   whose table the column reads matches on its columns (`_decides`). This is so in the Statement itself too: ticket 11's
   test asserted the step's own LEFT JOIN ON under `runs`; it now asserts it only under
   `alerts` (and under both with many_matches=True). The GROUP_BY key coming from the
   LEFT_JOIN (team) does not bring it in: it decides which group a row counts in, which the
   "One value for each different ..." line and the key's own lineage show, not whether it
   counts. Ticket 09's case was a different one: how-to 23's team write reads job_owners
   through a JOIN, with WHERE(equals(job_owners.dt, day)), a bound on the joined table's Date
   partition that its ON= sets equal to the day written. Like the day written itself (v2's
   ticket 22), it decides which day the write reads, not which rows a reader of many days
   counts, so it now shows only in the write's own section. A joined table's bound that isn't
   tied to the day written, as the starter's example 2 reads job_runs over two days, is still
   listed downstream (ticket 11's test holds it). Tests: test_lineage.py's
   `test_a_writers_left_join_decides_only_the_columns_read_from_its_table_downstream`,
   `test_a_left_join_decides_every_column_when_a_condition_reads_its_table`,
   `test_a_left_join_read_only_by_a_second_left_join_decides_only_what_that_one_brings` and
   `test_a_writes_bound_on_a_joined_tables_day_matched_to_the_day_written_stays_in_its_section`.
   Regenerated: both goldens (76 lines each, a LEFT JOIN ON under columns that don't read its
   table), both Example projects' lineage, and how-to 23 on both how-to pages (the weekly
   rollup no longer lists `equals(job_owners.dt, "2026-09-24")`). How-tos 13, 14, 23 and 29
   still read true: none of their prose names a LEFT JOIN ON or that bound.
3. **NaN job_id on sqlglot Composer's Example database.** sqlglot's own executor bug, the same
   on 25.24.2 and 30.19.0: to add rows up after a join, its `aggregate` works out each
   count's or sum's inside (an "operand", such as COUNT(*)'s `*` or count_rows(where=...)'s
   CASE) as new columns at the end of each row and calls `add_columns`, which widens every
   joined table's `column_range` by that many. A table's range then runs on into the next
   table's first columns, and its RowReader maps a shared name to the later index: for
   `FROM starts LEFT JOIN finishes ... GROUP BY starts.job_id`, starts.job_id reads
   finishes.job_id, NULL for each start with no finish. Not only Derived tables: two plain
   tables do it too. Refused, not fixed: while it runs a query, sqlglot Composer's engine wraps
   the executor's aggregate step and, before it runs, looks for a name the widening would
   remap in a table the groups or sums read; a JOIN (not LEFT_JOIN) whose ON sets the two
   equal is let through, since both hold the same value. The refusal is a RuntimeError, "The
   Example database can't run this Hive: its executor would mix up starts.job_id and
   finishes.job_id, two columns called job_id, ...", so a how-to's pandas stand-in can answer
   it; its fix says to wrap the column in AS(..., "finishes_job_id") in derived("finishes",
   ...) and read that name, which the executor then answers right. A first, simpler rule (any aggregate over a join to a table sharing a column
   name) refused right answers the gallery, how-tos and Example projects rely on, so the check
   follows the executor exactly. Tests:
   the refusal and a JOIN on the shared column still answered
   (tests/sqlglot_edition/test_sqlglot_example_database.py), and Spark Composer's right answer
   checked against pandas (tests/spark_edition/test_spark_intermediate_tables.py). No how-to,
   gallery entry or Example project ran that shape, so no page changed.
4. **A stray RepeatedRowsWarning when one Statement reads one block twice.** With both reads
   called runs_per_job, `JOIN(yesterday, ON=equals(yesterday.job_id, today.job_id))` compares
   runs_per_job.job_id with runs_per_job.job_id: `_matched_columns` can't count either side
   as the other table's, so the Warning said the join "matches on nothing", and statement(...)
   then refused the two names. The two can't be told apart from ON= alone (the Condition holds
   only aliases), and the same ON= from a table compared with itself is never meant either: it
   pairs every row with every row. So JOIN and LEFT_JOIN now refuse an ON= that sets a column
   of the joined table equal to the same column of a table of that name, before the Warning,
   with a ValueError and no opt-out, saying both sides are called runs_per_job, the name given
   to derived(...): give the second a name of its own, with AS for a Table reference or the
   same Derived table, or another name in derived(...) for a block built for other days (a
   Building block can take the name as an argument). An ON= comparing two different columns of that name (t.a = t.b)
   is left alone, since that can be a test within one row. Tests: test_refusals.py's
   `test_reading_one_block_twice_stops_at_the_join_with_no_repeated_rows_warning`,
   `test_one_block_read_twice_under_two_names_joins_with_no_warning`, and a `join_on_itself`
   case in test_misuse_refusals.py.

**Code review (2026-10-05).** Two reviews of 9d2193f (standards and spec), each fixed in the
next commit but where noted. Spec: a second LEFT_JOIN's ON= opened the gate for the first
under every column (FROM job_runs, LEFT_JOIN jobs, LEFT_JOIN job_owners on jobs.job_id: runs
listed jobs' ON=); only a condition that can drop rows opens it now, and a second LEFT_JOIN
passes the first on to the columns it brings, with a test. The beginner reader hadn't run on
the two new refusals: it has (below). Not changed: refusing some LEFT_JOINs whose rows all
match on sqlglot Composer's Example database (the reviewer turned the check off and the
executor did give a wrong answer, so it is right to refuse); patching the executor's
aggregate step on its class, which CI's two sqlglot jobs hold. Standards: the executor
refusal's fix had no example (now it names the AS(...) and the new column to read); the
clauses docstring was circular; "when they differ" in the Derived-table fix (now "built for
other days"); a comment on the ExecuteError's cause; `_date_bounds` had grown a third return
(now `_bounds_that_follow_the_day_written`); `_sets_equal`'s nested recursion (now a loop);
item 1's docstring now says CPython's own warnings.warn. Answered, not changed: the "equals
between two same-named columns" walk is in clauses.py, lineage.py and engine.py, but the last
reads sqlglot's trees and the other two ask different questions (a column with itself, two
given columns); the lineage boxes' string-keyed facts extend the existing pattern.

**Beginner reader (2026-10-05).** One read of the two new refusals, three stops each, fixed:
the JOIN refusal named runs_per_job where the user's variables were a and b (it now says
both are called runs_per_job, the name given to derived(...)); "each row before the join"
(now "every row of the tables before the join"); AS(runs_per_job, ...) on a name the user has
no variable for, against how-to 24's "keep each block's name the same" (now: built for other
days, another name in derived(...), "runs_per_job_earlier", the block taking the name as an
argument; the same one twice, AS(it, "earlier")). The executor refusal: "adds up rows" (now
"works out GROUP_BY and the counts and sums"); "make the two names differ" (now which column,
the AS(...) and the name to read in ON=); a Table reference (now: it can't be renamed, read it
through a Derived table that does).
