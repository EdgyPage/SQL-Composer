# Every row of the conversion chart checks out

Type: task
Status: resolved
Blocked by: 08, 09
Size: L

## Question

On 2026-10-26, after 7.2's tickets were resolved, five queries of other people's Hive were run
through `project.convert` in a copy of the Intermediate Example project, and each converted
Statement compared with its original, by its Hive and by its rows on the Example database; a
script of two INSERTs from one FROM, and a DROP, were refused as a Conversion refuses them. The
queries are in `tests/test_conversion_chart.py`'s `CHART`. The chart of the results had three
gaps, which the user asked to have fixed, "test-first, with a
ticket and the usual reviews", and then: "Fix the gaps in the conversion chart as well. Model
what you need to confirm functionality in the test suites."

1. **A subquery in FROM was reported as a different query.** `SELECT * FROM (SELECT ...) ranked`
   converts to a Derived table, which the Toolbox writes as `WITH ranked AS (...)`. The two are
   the same query, but `compare_hive`, and so the Conversion's own summary, said line 1
   differs.
2. **An original that gives `*` can't be compared by its rows.** `compare_with_original` reads
   the original's column names from its SELECT, and refuses a `*`, whose names it can't see,
   though the tables the original reads say what they are.
3. **The Example database couldn't run two of the five.** Its executor, sqlglot's own, refused a
   GROUP BY after a join of two tables that share a column name (`job_id`), and has no window
   functions, so `ROW_NUMBER() OVER (...)` couldn't be checked against its original.

## Done when

- `compare_hive` treats a subquery in FROM or JOIN as the Derived table, the WITH, it is: the
  two are the same query once both are written out the same way. Its docstring says so.
- `compare_with_original` takes an original whose SELECT gives `*` or `t.*`, finding the names
  from what it reads: a Derived table or subquery of the original, or a table the Statement
  reads, by its Table reference. A `*` over a table it can't tell is still refused, as now.
- The Example database adds rows up after any join correctly, so it no longer refuses one whose
  tables share a column name: the executor's own slip, which widened each joined table into the
  next one's columns, is mended while a query runs.
- The Example database runs windows: `row_number`, `rank`, `dense_rank`, `ntile`, `lag`, `lead`,
  `first_value`, `last_value`, and `sum_of`, `average_of`, `count_rows`, `min_of` and `max_of`
  with `over=`, with PARTITION BY, ORDER BY (NULL first ascending, as Hive) and `rows=`, as
  Hive gives them. A window it can't work out is refused as a missing part, as now.
- A test converts each of the chart's queries on the Intermediate Example project and checks
  both: its Hive is the original's, and its rows are the original's on a Partition that has
  rows. Each query of the chart, the refusals included, is in the suite.
- Every how-to and gallery entry that showed the window refusal, or worked a window's result
  out in pandas because of it, runs it on the Example database instead.
- CHANGES.md's 7.2 names each; CLAUDE.md's Definition of done, the beginner reader included.

## Answer

Built 2026-10-26, test-first, in 031d36a and the fix after it.

- **The Hive.** `normalised_query` writes each query in brackets in FROM or JOIN as a WITH,
  with sqlglot's `eliminate_subqueries`, on both sides, so a Derived table and the subquery it
  was converted from are one query where the name after the bracket is the Derived table's.
- **The `*`.** `_stars_named` writes a `*` or `t.*` as the columns it stands for, where they
  can be found: a Derived table's or a query's in brackets, or a table's the Statement reads,
  by its Table reference, partition columns last, as Hive gives them. Both compares use it. A
  `*` over a table the Statement doesn't read is still refused, its fix saying why.
- **The join.** sqlglot's executor widened each joined table into the next one's columns when it
  added rows up; `_joined_tables_kept_apart` keeps each to its own while a query runs, so the
  mix-up refusal is gone, and the test that showed it now checks the right counts.
- **Windows.** Each SELECT with a window runs without it, its rows giving each value the
  windows read; the windows are worked out from those rows as Hive works them out, and the
  SELECT reads them from a table made of them. What it can't work out (RANGE with a number,
  IGNORE NULLS, PERCENT_RANK and the like, COUNT(DISTINCT) over a window, a window outside
  SELECT) is refused plainly. How-tos 10, 13 and 17 and latest_and_top_n lost their pandas
  stand-ins; their pages give the same rows as before, which checks the windows against the
  pandas that stood in.
- **Not asked for, needed by the chart:** a CASE on one column is spelt out as CASE WHEN
  before the executor runs it, as it wrote Python's = for == beside a count. And the how-to
  page refuses a pandas stand-in the Example database never needed, as how-to 13's slipped
  through (D283).

## Reviews

- Beginner reader: [reports/10-beginner-reader.md](../reports/10-beginner-reader.md), stop by
  stop:
  - 1 (the name after the bracket): fixed, compare_hive's docstring says the name must be the
    Derived table's.
  - 2 ("where they can be told"): fixed, the docstrings say "where the Toolbox knows them".
  - 3 (partition columns last): fixed in compare_hive's docstring and CHANGES.
  - 4 (a * over a table not read): fixed, the refusal's fix says the Toolbox doesn't know its
    columns, and to list them in place of the *.
  - 5, 6, 7 (the refusals' grammar): fixed, each reads after "has no", and the RANGE and ORDER
    BY ones say what runs instead.
  - 8 (fix points at the Statement): fixed, every missing part's fix says to try the rest
    without it, in the Statement or in the original Hive.
  - 9 (how-to 13): fixed, D283.
  - 10 (counting down): fixed, how-to 10 says the rows come by job and event id.
  - 11 (1.0 then 1): answered, how-to 17 says NaN makes pandas show decimals, before both.
  - 12 (top N by run): fixed, top_runs_per_job's docstring says the order.
  - 13 (the gallery's label): answered, the gallery's layout for a docstring of two Statements,
    unchanged here.
  - 14, 15, 16 (CHANGES): fixed.
- Code review of 031d36a (2026-10-26):
  - Spec: fixed, how-to 13 (D283); IGNORE NULLS and NTILE(0) are refused plainly, tested; the
    Question names five queries and two refusals, all in the suite; tests added for NULLS LAST,
    ROWS ... FOLLOWING and RANGE to UNBOUNDED FOLLOWING. Answered: the CASE spelling and the `*`
    in compare_hive are what the chart needed, and named here and in CHANGES; 7.0's change
    note of the mix-up refusal is history, left as it was.
  - Standards: fixed, the refusals' grammar; "frame" and "partition", the glossary's words to
    avoid for a Window's rows and groups, are gone from the window code (`rows_near`,
    `groups`, `_rows_looked_across`); `_place` is `_where_in_with` and its closure `read_at`;
    `end_of`'s hint is `str | exp.Expression | None`; an ORDER BY column is an `_Ordered`, not
    a bare tuple; query_columns and `_columns_read` share `_names_given`; no `sum(found, [])`.
    Answered: the window functions branch on sqlglot's name in three small functions, as the
    standards prefer plain functions to a table of them; `schema` keeps
    `_stacked_reads_told_apart`'s older hint, which this ticket didn't touch.
- Drift: D283 to D285 fixed in the commit after 031d36a.
