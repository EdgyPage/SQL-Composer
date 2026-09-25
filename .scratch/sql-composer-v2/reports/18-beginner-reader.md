# Beginner-reader report: Toolbox core (ticket 18)

Run on `dev` after the Toolbox core was built (commits 0089c86..e9bbfc7), by
`.claude/agents/beginner-reader.md`. Advisory only: the user decides what changes.

The reader read the cheat sheet (first docstring lines in `__all__` order), every public
docstring, and `test_currently_failing` from `tests/test_style_b_statements.py`, run with
`python -c`. It then provoked 8 refusals and a warning. Durations: **moment** (under 30 s),
**reread**, **stuck** (could not go on without outside help).

## Top 3 costliest stops

1. **The Example database can't run the Toolbox's own `row_number` and `week_start` Statements,
   and fails with a raw sqlglot traceback.** `calculations.py:281` says "The Example database shows
   both". Running `test_currently_failing` crashes with `ExecuteError ... ROWNUMBER() OVER`, and
   `test_failed_by_week` with `name 'NEXTDAY' is not defined`. The error doesn't say the Statement
   itself is fine. Related silent case: `starts_with`/`contains` with `_` or `%` return an empty
   result on the Example database. Stuck.
2. **Where do `job_runs` and `jobs` come from?** Every docstring example uses them bare
   (`tables.py:466`, `592`, and all of clauses, conditions and calculations). The import line at
   `__init__.py:5` doesn't bring them, and the only hint, `example_database.py:9`, uses
   `example_database.job_runs` under another name. Stuck.
3. **`send` is required from the second cheat-sheet line but explained ~50 names later.** It first
   appears at `tables.py:697-705` (`write_table_reference(name, send)`) and is defined only at
   `running.py:3-4` / `running.py:261`. Stuck, then resolved late.

Close behind: `CROSS_JOIN`'s "its name is the opt-out" (`clauses.py:332`), unclear until reading
`refusals.py`; and the `LEFT_JOIN` docstring's unexplained `many_matches=True` plus an unbounded
`FROM(jobs)` (`clauses.py:310-316`).

## A. Cheat sheet

1. `Table` (`tables.py:446`): two capitalised terms at once ("Table reference", "Date
   partition"). Reread, then CONTEXT look-up.
2. `write_table_reference(name, send)` (`tables.py:698`): `send` required, never said what it is
   until `running.py`. Stuck (carried open).
3. Order: the first seven names are all table setup and warehouse checks; no `SELECT` in sight.
   Reread.
4. `create_table` (`tables.py:942`): "Saved table". CONTEXT look-up.
5. `FROM` (`clauses.py:219`): "its Date partition must be bounded in WHERE". CONTEXT look-up.
6. `CROSS_JOIN` (`clauses.py:332`): "its name is the opt-out" - of what? `JOIN`'s docstring
   doesn't say `ON=` is required; its signature shows `ON=None`. Stuck until `refusals.py`.
7. `sum_of(..., adds_up=False)` / `average_of`: read as "by default this doesn't add up". Reread.
8. `row_number(*, PARTITION_BY, ORDER_BY)`: keyword shares the clause's name; `PARTITION_BY` is a
   third meaning of "partition". Reread.
9. `run(s, send)`: "your `send` function" - the first explanation. Moment.
10. `GuardRefused` / `LoadRefused`: more capitalised terms. CONTEXT look-up.
11. `example_database`: "a send" used as a noun. Moment.

## B. Docstrings

- `__init__.py:5`: the import line doesn't bring `job_runs`/`jobs`. Stuck (Top 3 #2).
- `tables.py:454-455`: `date_partition` "is required ... or None". Reread.
- `tables.py:466`, `592`: `job_runs`, `jobs` never defined. (Top 3 #2)
- `tables.py:609`: "bounded to the day before today like any other" read as every Statement being
  silently bounded to yesterday. Reread.
- `tables.py:707-716`: `# low / high` is Hive's column comment, unsaid; why is a date column a
  string? Moment.
- `tables.py:944-947`: one long sentence with three ideas. Reread.
- `tables.py:953-960`: `dt` moves to `PARTITIONED BY`; `STORED AS ORC` unexplained. Reread.
- `CONTEXT.md:36-37` and `tables.py:737-738`: a Table reference holds "filters", but `Table(...)`
  has no filters argument. Moment.
- `clauses.py:92` vs `97-98`: "comes out bracketed", but the example has no brackets (only nested
  arithmetic gets them). Reread, then ran it.
- `clauses.py:175-189`: the first clause example already uses `AS`, `count_rows`, `last_n_days`,
  `GROUP_BY`. Moment.
- `clauses.py:186`, every `last_n_days`: examples assume today is 2026-09-25, never said.
  Reread.
- `clauses.py:198-202`, `310-316`, `336-346`, `484-488`: `FROM(jobs)` with no WHERE and no
  refusal, right after "must be bounded"; `jobs` having `date_partition=None` is only in source.
  Reread / look-up.
- `clauses.py:280-282`: key-pinning prose; why is `ON=` upper case? Reread.
- `clauses.py:306-316` (`LEFT_JOIN`): dense; `many_matches=True` unexplained;
  `count_rows(where=is_not_null(...))` needed thought. Reread.
- `clauses.py:319`, `conditions.py:372`, `353`: `NOT x IS NULL`, `NOT x IN (...)` instead of the
  familiar `IS NOT NULL` / `NOT IN`. Moment each.
- `clauses.py:397`, `calculations.py:212-216`: `NEXT_DAY(DATE_ADD(dt, 7 * -1), 'MO')`; the reason
  is only at `running.py:228-229`. Reread.
- `clauses.py:500-505` (`INSERT_OVERWRITE`): "the one day the Statement reads" has to be inferred;
  "Tez ... HIVE-18702" is jargon. Reread.
- `clauses.py:514`: why `GROUP_BY(job_runs.dt, ...)` when `dt` isn't selected? Reason only in
  `running.py:352-353`, `refusals.py:235-247`. Reread, unresolved.
- `clauses.py:783-786` (`derived`): "WITH part", "Statement part"; the parameter is named
  `statement`, like the function. Reread.
- `conditions.py:163-164`: `'O\\'Brien'` (two backslashes in source, one in `help()`); expected
  `'O''Brien'`; odd example. Reread.
- `conditions.py:396`, `407-408`: "% and _ matched as themselves", `LIKE 'invoice\\\\_%'` - LIKE
  wildcards unknown, backslash count unclear. Stuck.
- `calculations.py:5`: "aggregates ... end in `_of`", but `count_rows`, `count_distinct` don't.
  Moment.
- `calculations.py:111-115` (`average_of`): first line about input, next about output; what does
  `adds_up=True` do here? Reread.
- `calculations.py:279-281` (`row_number`): "The Example database shows both" - it doesn't, and
  running it crashes. Stuck.
- `calculations.py:251`: `descending`'s example is a `row_number`, not `ORDER_BY`. Moment.
- `calculations.py:296`: "sqlglot" - what is that, to a user? Moment.
- `running.py:42-44` (`set_load_limits`): "refuses a result that fills it". Reread.
- `running.py:349`: `run_query` never introduced (also in the refusal at `running.py:279`).
  Moment.
- `running.py:351-353` (`by_day`): dense. Reread.
- `running.py:361-382`: two Statements printed back to back, no separator. Moment.
- `example_database.py:9`: `runs = example_database.job_runs` - different name from every other
  example. Reread.

## C. Glossary look-ups

Table reference (`tables.py:446`), Date partition (`tables.py:454`, `clauses.py:219`), Saved
table (`tables.py:942`), Guard / Load limit (`clauses.py:7`, `refusals.py:1-5`). CONTEXT answered
each, apart from the "filters" oddity. "Derived table" appears in messages (`refusals.py:263`,
`tables.py:800`) but never in the `derived` docstring. Moment.

## D. The Statement run (`test_currently_failing`)

- `tests/test_style_b_statements.py:32`: `from sql_composer.example_database import job_runs as
  runs` - the first place the import is shown. Reread.
- The Python calls it `runs`, the Hive says `job_runs`: the alias comes from the table name.
  Reread.
- The `WITH ranked AS (...), latest AS (...)` Hive matched the test. Moment.
- `run(s, send=example_database.send)` on sqlglot 30.19.0 crashed with a raw
  `sqlglot.errors.ExecuteError` (`ROWNUMBER() OVER ...`), not a four-part message. Research issue
  14 already records "No window functions at all" and "Hive date functions fail"; nothing tells
  the beginner. `test_failed_by_week` also crashes (`name 'NEXTDAY' is not defined`).
  `test_failures_by_team` runs and gives `finance 1`, checked by hand.
- **Silent wrong answer on the Example database:**

  | Condition | Rows returned |
  |---|---|
  | `starts_with(jobs.job_name, "invoice")` | `['invoice_sync']` |
  | `starts_with(jobs.job_name, "invoice_")` | `[]` |
  | `contains(jobs.job_name, "_sync")` | `[]` |

## E. Refusals and a warning provoked

The four-part shape is easy to read, and all eight gave an actionable fix. Stops:

- `LEFT_JOIN` then `WHERE(equals(job_runs.status, "FAILED"))`: the `RepeatedRowsWarning` printed
  before the `GuardRefused`, so the reader fixed the wrong thing first; the warning's fix "Group
  job_runs first ..." (`refusals.py:274`) doesn't say how. Reread.
- `sum_of(job_runs.avg_retry_secs)`: "a user seen on two days would be counted twice"
  (`refusals.py:136-138`) - no users here, and the column is an average. Moment.
- `WHERE(job_runs.status == "FAILED")`: a `TypeError` with "Opt-out: none" is noise; several
  four-part messages are `TypeError`/`ValueError`, not `GuardRefused`. Moment.
- `equals(job_runs.duration_mins, "30")`: "a int column" (`tables.py:275`). Moment.
- `refusals.py:228`: capital "Partition". Moment.
- `refusals.py:371`: the dates-cap opt-out `reads_all_partitions=True` when the reader wanted 40
  days, not all. Moment.

Clear, no stop: `equals(..., None)`, `JOIN(jobs)` without `ON`, a date written `"24/09/2026"`,
clauses out of order.
