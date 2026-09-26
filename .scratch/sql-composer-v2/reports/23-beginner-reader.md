# Beginner reader: "Add `INSERT_INTO` and `drop_table`"

Run on 2026-09-26, from `63ebaaa` to `76b5b30`. The beginner reader may not write files, so the
session saved its report here as it was given. Line numbers are at `76b5b30`.

Read: the cheat sheet (first docstring lines in `__all__` order); the docstrings of
`INSERT_OVERWRITE`, `INSERT_INTO`, `create_table`, `drop_table`, and of `by_day`, `run`, `JOIN`,
`LEFT_JOIN`, `all_of`, `contains`, `derived` where the new examples lean on them; the write
refusals, triggered by hand; `CHANGES.md` 2.1; the gallery paragraph of
`docs/clean-branch-readme.md`; the six new Worked examples and `table_references/runs_to_review.py`;
the gallery's new "Worked examples of common jobs" section. `saved_table.py` was read start to
finish, each step run with `to_hive`.

## A. Things that look wrong or risky against the scripts

- **A1. `backfill()` and `rebuild()` lose the alerted runs after step 3.** `saved_table.py:79-99`:
  step 4 rewrites each day with `INSERT_OVERWRITE` of the failed runs only, so the alerted runs
  step 3 added to 2026-09-24 are wiped; `rebuild()` then says to "write them all again with
  backfill()". The example teaches a routine that quietly drops half of what the table holds.
- **A2. `INSERT_INTO`'s docstring example is the case its own text warns against.**
  `clauses.py:602-613`: the text says "Use it when a day is filled by more than one Statement,
  such as one for each source", but the example is one per-job `COUNT(*)` from one source, which
  sent twice doubles every count. Even with a real second source, a per-job count added twice
  gives two rows per job, which a reader must `SUM`.
- **A3. `drop_table` takes any real table, source tables included, with no warning.**
  `drop_table(example_database.job_runs)` returns `DROP TABLE IF EXISTS ops.job_runs`. The cheat
  line reads "for a table" (`tables.py:1068`), where `create_table`'s reads "for a Saved table";
  `create_table` (`tables.py:1029-1030`) gives "drop it first with drop_table(t)" as the first
  remedy without saying it deletes every day.
- **A4. The refusal for two writes doesn't name the problem.** `statement(INSERT_OVERWRITE(t),
  INSERT_INTO(t), ...)` says the clauses are "out of SQL order, or one clause twice", and the fix
  gives an order the Statement already has; nothing says "a Statement has one write". The same for
  `SELECT` beside `SELECT_DISTINCT`.
- **A5. `lists_and_text.py:3`'s Why says "these three jobs"**, but the Statement lists two.

## B. Stops, costliest first

1. **Stuck:** why use `INSERT_INTO` in its own example (A2)? "source" could mean a table, a
   system or a Statement, and the gallery can't show what "keeps them and adds more" does to a
   day's rows. Would help: the day's rows after each step, worked out in pandas.
2. **Stuck:** does 2026-09-24 still hold the alerted runs after step 4 (A1)? Step 4 also gives no
   reason to write past days, and "backfill" is never defined.
3. **Reread, worried:** what may I drop (A3)? "can't be undone from here": undone somewhere else?
4. **Reread:** why two Statements rather than one `any_of`? Because the second reads `run_alerts`,
   joined; one clause saying so would answer why this is `INSERT_INTO`'s job.
5. **Reread, no way forward:** HIVE-18702 (`clauses.py:569-570`). What is Tez, am I on it, and
   what do I do if a day may come back empty?
6. **Reread:** the two-writes refusal (A4).
7. **Reread:** "Keep rows by a list..." sits above "Keep a Saved table...", and WHERE's cheat line
   says "Keep only the rows": "Keep a Saved table" first read as a filter.
8. **Reread:** where did `dt` go? It isn't selected, since `PARTITION(dt = ...)` fills it, and
   the docstring examples' `GROUP_BY(job_runs.dt, ...)` is there only for `by_day`.
9. **Reread:** "matched by name" (`clauses.py:566`) against "Hive fills ... by position"
   (`refusals.py:236`) look like a contradiction on first read.
10. **Reread:** `step_by_step.py:55` tests a total in WHERE, just after `groups_and_top_n` said
    WHERE can't test a count; a Derived table's totals are plain columns to the next step.
11. **Reread:** "can't quietly look like it changed the table" (`tables.py:1028-1029`,
    `saved_table.py:27-28`): the negatives stack up.
12. **Reread:** `LIKE '%\\_build%'`: why two backslashes?
13. **Reread:** the README's "Worked examples on their own" reads as "separately"; the gallery's
    "scripts kept where the Toolbox is written" doesn't say where that is.
14. **A moment:** `INSERT_INTO`'s cheat line gives no warning, and every SQL tutorial makes
    `INSERT INTO` the normal way to add rows.
15. **A moment:** which day does `alerted_runs` write, when it reads two tables bound to the day?
16. **A moment:** the no-Date-partition refusal's fix changes the question: how would I save a
    daily copy of `jobs`?
17. **A moment:** "one day's Partition" (`refusals.py:250-251`) sent me to `CONTEXT.md`.
18. **A moment:** `run_query` is used as if defined.
19. **A moment:** what does `run` return for a DROP or a write?
20. **A moment:** `from table_references.runs_to_review import ...` fails when pasted.
21. **A moment:** `INSERT OVERWRITE TABLE` against `INSERT INTO`; `STORED AS ORC` unexplained.
22. **A moment:** capitals for `INSERT_INTO`, lower case for `drop_table`.
23. **A moment:** `key=["run_id"]` doesn't stop doubles; only `check_key`/`JOIN` say Hive never
    enforces a key.
24. **A moment:** `all_of`'s cheat line says "for use inside any_of", but it is used in `ON=`.
25. **A moment:** the outcome counts don't add up to the runs: the TEST run is in no column.
26. **A moment:** `NOT job_runs.status IN (...)` isn't the `NOT IN` I know.
27. **A moment:** "the four shapes that answer 'how many per something'", but `teams()` counts
    nothing.
28. **A moment:** "a sum of counts of different values" means `count_distinct`.
29. **A moment:** `CHANGES.md:18` "... beside their fix follow": "follow" read as a verb first.
30. **A moment:** two "Step 1"s in `saved_table.py`.
31. **Lookups in `CONTEXT.md`:** "Saved table" at `create_table`'s cheat line; "Partition" at 17.
32. **Fixed at `76b5b30`:** `drop_table("mart.runs_to_review")` no longer calls a string a
    Derived table.

What read well: the why in `saved_table.py:3-4`; "That makes it the safe first write of each
day"; `drop_table`'s reason; `jobs_that_never_ran`'s ON-not-WHERE explanation; `CHANGES.md:7-10`,
the clearest statement anywhere of when to use each write.

## C. The three costliest stops

1. **B1 / A2:** `INSERT_INTO`'s docstring example shows the case its own text says doubles.
2. **B2 / A1:** `saved_table.py`'s `backfill()` and `rebuild()` wipe step 3's rows.
3. **B3 / A3:** `drop_table` is "for a table" and takes a source table without a word.
