# One bottom read for by_day, writes and lineage

Type: task
Status: claimed
Blocked by: 01

## Question

by_day, a write's one-day Guard and export_lineage all need the same thing: the real table at
the bottom of FROM, following Derived tables down, with its Date partition and the days it
reads. The review (candidate 2 of [report.html](../report.html)) found that each finds it its
own way, and that by_day's check on the steps above compares names:

1. **by_day splits a top-N across days.** `_check_splittable` (`running.py:294`) never looks at
   LIMIT, so `ORDER_BY(...) + LIMIT(10)` over a week becomes the top 10 of each day: 70 rows,
   with no refusal.
2. **by_day matches the Date partition by bare name.** Any table's column called `dt` counts as
   keeping the date, and so does any output called `dt`. Meanwhile a `dt` renamed with
   `AS(job_runs.dt, "day")` in a Derived table is refused, though it keeps the date.
3. **by_day's refusal for a FROM table with no Date partition names a column it lacks**
   (`between(jobs.dt, ...)`), and repeats `_written_day`'s two checks in other words.
4. **The walk down FROM is written three times**: `_steps`, `_bottom_read` and
   `lineage._date_bounds`.
5. **export_lineage refuses a write over several days when a dates cap is set**, though it
   draws a write over several days by sending its first day (`lineage._submitted`).
6. **The dates cap's fix for a joined table says to use by_day**, which splits only the table
   in FROM, so the same refusal comes back for each day.
7. **Untested:** by_day on a SELECT_DISTINCT or a total, and the dates cap through a Derived
   table.

## Decisions (the user asked for this candidate on 2026-10-03; the rest are the agent's)

- **The date is followed as a column, not a name.** At the bottom step it is the FROM table's
  Date partition column; at each step above, it is the Derived table's output whose
  calculation is that column, under whatever name the output has. A step keeps the date when
  that column is in its GROUP_BY, its DISTINCT outputs or each window's PARTITION_BY.
- **by_day refuses a LIMIT at any step**, with a Guard of its own: LIMIT keeps rows of the
  whole Statement, and a split keeps them per day. Run the Statement whole instead.
- **One walk** (`steps`), in running.py, which lineage uses too. by_day and a write share one
  check that the bottom table has a bounded Date partition, with one wording.
- **export_lineage shows a write over several days by its first day, dates cap or not.** A read
  over the cap is still refused, as to_hive refuses it: the report shows the Hive as
  submitted.
- **The dates cap's fix depends on the table:** for the table by_day splits, by_day; for any
  other, narrow that table's own bound.

## Done when

- Each of 1-7 has a test through the public names, run in both Editions; every new refusal is
  four-part.
- Both runs pass; goldens and galleries regenerated if their text changed.
- The code-review skill has run with this ticket as its spec, the drift items are closed, and
  the beginner reader has read the new refusal text.
