# Beginner reader: the texts changed by the user's decisions (2026-09-25)

Run by `.claude/agents/beginner-reader.md` over only the beginner-visible texts changed since
12f0c3f, at c502537: the re-grouping Guard's "Usual fix", the missing-`GROUP_BY` Guard's
"Usual fix", `CROSS_JOIN`'s docstring, the new sentence in `ORDER_BY`'s docstring, and the
import stop for files from two exports. It ran each refusal, and `careless()` from the
re-grouping Worked example. Its report, as given; it only advises, and the user decides.

## Stops

1. `refusals.py` `_REGROUPING_FIXES["a distinct count"]`: "Count again from the rows it was
   counted from, with count_distinct(...) under your own GROUP_BY". In `careless()` I'm
   holding `jobs_per_day`, a Derived table. "the rows it was counted from" doesn't say that
   means going back to `job_runs`, and "your own GROUP_BY" made me ask whose GROUP_BY the other
   one is. The example after the colon ("a week's count comes from the week's rows") cleared it
   up. **Reread.**
2. The same fix shown under `average_of`. `average_of(daily.per_day)` is refused with
   "average_of(daily.per_day) adds up daily.per_day" and the fix says "rather than adding up
   the smaller counts". I wasn't adding anything up. I wanted the average number of jobs per
   day, and I couldn't tell whether that is wrong. **Stuck.**
3. `_REGROUPING_FIX_FOR_A_LISTED_COLUMN`: "It could be an average, a ratio or a distinct count.
   For an average or a ratio, keep the two parts it was made from". `job_runs.avg_retry_secs`
   is a column in a table someone else built, and I can't see any "two parts" in `job_runs` to
   keep. So the advice doesn't say what to do with a Saved table. I had to guess the column's
   kind from its name. **Reread, close to stuck.**
4. `_REGROUPING_FIXES["an average"]`: "(the sum and the count)". Which count? The only public
   counts are `count_rows` and `count_distinct`. I guessed `count_rows()`. **A moment.**
5. `guard_missing_group_by`: "Add job_runs.status to GROUP_BY. To keep one whole row per group
   instead, such as each job's latest run, number the rows with row_number(...) inside
   derived(...)". It doesn't say that this route drops my GROUP_BY and my `count_rows`, which
   is the "runs" column I asked for. It also doesn't say that number 1 is the latest only if
   the sort is `descending(...)`. `help(row_number)` answers both. **Reread.**
6. Same text: "WHERE(equals(..., 1))". I briefly read `...` as Python's Ellipsis. It stands for
   the row-number column's name in the Derived table. **A moment.**
7. `clauses.py` `CROSS_JOIN` first line: "Pair every row with every row of another table, with
   no ON=." It is clear. The body's "CROSS_JOIN is the opt-out of that refusal" matches what
   `JOIN(jobs)` actually prints. Then comes "Joining a table to itself needs a second name for
   it", and the example is a self-join with no reason given for why anyone would pair every job
   with every job. `reads_all_partitions` is not explained. **A moment.**
8. `ORDER_BY`: "an ORDER_BY without LIMIT is refused even with sorts_everything=True: Hive
   ignores the order of rows there". It is true: I checked that `derived('d', ...)` refuses.
   The refusal comes from the `derived(...)` call, not from `statement(...)`, which surprised
   me at first. **A moment.**
9. `__init__.py` `_check_files`: "Two exports of the same Toolbox version can differ, so the
   code, the Example gallery and the change notes". I don't know the word "export", and I had
   to map "Example gallery" to `examples.html` and "change notes" to `CHANGES.md` (I checked
   CONTEXT.md:113). The message also ends with "Opt-out: none - this one can't be switched
   off.", which is strange on an import stop. None of the other import stops has an Opt-out
   line. **Reread.**

## The three costliest

1. Stop 2: the distinct-count fix shown under `average_of`.
2. Stop 3: the fix for a listed column in a Saved table.
3. Stop 5: the row_number route drops the grouped count without saying so.

## Outright bugs

1. **Advice that leads to a wrong result: the distinct-count fix under `average_of`.** The
   Guard refuses `average_of` on a distinct count, and the shared fix points to "a week's count
   comes from the week's rows". The average of daily distinct counts is a valid number
   (average jobs per day). Following the fix literally returns the weekly distinct count
   instead, a different and wrong answer for that question. The "What happened" line also says
   "adds up" for an `average_of` call. That line is older text, but the new fix repeats the
   same framing.
2. **Advice that can't be followed, and may be wrong: the fix for a listed column.** For a
   column listed in `does_not_add_up` on a Saved table like `job_runs.avg_retry_secs`, "keep
   the two parts it was made from" can't be done: the parts aren't in the table. The
   distinct-count half ("count again ... from the rows it was counted from") has the same
   problem, since those rows aren't available.
3. **Possible wrong result: "the sum and the count" in the average fix.** `AVG` leaves out
   NULLs, while `count_rows()` counts every row. A beginner who divides `sum_of(x)` by
   `count_rows()` gets a smaller average whenever `x` has NULLs. The fix should say
   `count_rows(where=is_not_null(x))`, or say which count.

The CROSS_JOIN, ORDER_BY and missing-GROUP_BY texts are accurate. It found no false statement
in them.
