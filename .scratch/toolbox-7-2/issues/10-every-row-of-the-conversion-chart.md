# Every row of the conversion chart checks out

Type: task
Status: in progress
Blocked by: 08, 09
Size: L

## Question

On 2026-10-26, after 7.2's tickets were resolved, six queries of other people's Hive were run
through `project.convert` in a copy of the Intermediate Example project, and each converted
Statement compared with its original, by its Hive and by its rows on the Example database. The
chart of the results had three gaps, which the user asked to have fixed, "test-first, with a
ticket and the usual reviews", and then: "Fix the gaps in the conversion chart as well. Model
what you need to confirm functionality in the test suites."

1. **A subquery in FROM was reported as a different query.** `SELECT * FROM (SELECT ...) ranked`
   converts to a Derived table, which the Toolbox writes as `WITH ranked AS (...)`. The two are
   the same query, but `compare_hive`, and so the Conversion's own summary, said line 1
   differs.
2. **An original that gives `*` can't be compared by its rows.** `compare_with_original` reads
   the original's column names from its SELECT, and refuses a `*`, whose names it can't see,
   though the tables the original reads say what they are.
3. **The Example database couldn't run two of the six.** Its executor, sqlglot's own, refused a
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
