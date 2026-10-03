# One bottom read for by_day, writes and lineage

Type: task
Status: resolved
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

## Answer

Built in `69f3089`, reworked after the review in `52c2ba3` and after a second beginner reading
in `8a13bda`.

- `running.steps(s)` is the one walk down FROM, and `bottom_read(s)` the FROM read at its
  bottom with its days; by_day, a write, the dates Load limit and lineage all use them.
  `_bottom_days` is the one check that the FROM table has a bounded Date partition. by_day and
  a write share its "what"; each keeps its own "who", "why" and fix for a table with no days,
  which the beginner reader asked for, since by_day can run whole and a write can't. An
  opted-out read (`reads_all_partitions=True`) is named as one, also at the reader's asking.
- by_day follows the Date partition as a column up through each Derived table, under every
  name a step gives it, and refuses a step that drops it from its GROUP_BY, SELECT_DISTINCT or
  row_number's PARTITION_BY, naming it as that step sees it (`per_day.day (job_runs.dt, the
  Date partition)`), or saying to keep it in the SELECT of the Derived table that dropped it.
- `guard_by_day_limit` refuses a LIMIT in the Statement or a Derived table by_day reads
  through FROM; a joined Derived table's LIMIT isn't split, so it is let through.
- export_lineage falls back to the first day only for a write over several days, so a one-day
  write over the dates Load limit is refused as to_hive refuses it.
- The dates Load limit's fix sends the FROM table to by_day and any other table to its own
  between(...) or last_n_days(...).
- `tests/test_by_day_splits.py` pins items 1-3 and 5-7 in both Editions. Item 4, the single
  walk, is internal: what it holds is that by_day, writes and lineage agree, which those tests
  see.

**Beginner reader:** [first reading](../reports/02-beginner-reader.md), 9 stops; a second
reading of the reworded grouping refusal had 6 stops, all answered: the fix for a Derived
table that dropped the date, the partition named as the step sees it, the clause named
(GROUP_BY(...), SELECT_DISTINCT(...) or row_number's PARTITION_BY), refusals.py's "by_day(...)
refuses any LIMIT", and CHANGES' wording for set_load_limits(dates=...).

**Code review (2026-10-03), `69f3089`.**
- *Standards:* "date column", which the glossary rules out, removed; "dates cap" replaced in
  what a user reads; local names; the walk hidden behind `bottom_read`. Kept: `steps` returns
  each step with the words a refusal names it by, since only refusals use them.
- *Spec:* a one-day write over the dates Load limit got by_day's refusal from export_lineage;
  the grouping refusal named `dt` where the step calls it something else; only the first
  output carrying the date was followed. All three fixed, with tests.

| Items | Opened by | Closed by |
|---|---|---|
| D101-D104 | `69f3089` | `52c2ba3` |
| D105 | `52c2ba3` | `8a13bda` |
