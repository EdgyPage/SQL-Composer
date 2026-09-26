# Beginner-reader report: the Example gallery (`sql_composer/examples.html`), README paragraph, CHANGES.md line

Run for "Build the Example gallery" (ticket 20) on 2026-09-25, over `dev` at `7df509c`. The
report is advice for the user; see the ticket's Comments for what was fixed.

I read the Example gallery, the README paragraph and the CHANGES.md line as a beginner would,
and found no wrong number. But on the Clean branch two of the seven Worked examples can't be
pasted into a notebook as they stand. Any pasted docstring example that reads recent days
(`last_n_days`, `first_look`) also quietly gives different dates once today isn't 2026-09-25
(dates past 2026-09-25 return no rows).

## What I read

- **Gallery:** `sql_composer/examples.html`, top to bottom, skipping the `<style>` and
  `<script>`. That covers the introduction, all 7 Worked examples on their own and all 61
  docstring entries, including every one you listed.
- **Cheat sheet:** printed in memory with `tools/export_clean.py`'s own
  `describe_toolbox()`/`cheat_sheet()`. No file was written.
- **Docstrings:** the ones behind the gallery entries, in `sql_composer/*.py`.
- **One Worked example from start to finish:** `worked_examples/statements/regrouping.py`. I
  ran its `careless()`, `careless(adds_up=True)`, `fixed()` and the pandas helpers. I also ran
  `careless()`/`fixed()` for the other six.
- **README and CHANGES:** `docs/clean-branch-readme.md` lines 70-84 and
  `sql_composer/CHANGES.md` lines 35-40.
- **Glossary:** I opened `CONTEXT.md` once, when "Worked examples on their own", "Building
  block" and "Saved table" stopped me. That is counted as a stop below.

Nothing was edited, created or committed.

## Check for false content

**Numbers.** Every result table agrees with the rows in `sql_composer/example_database.py` and
with the Statement shown. I checked each one by hand, and I ran all seven Worked examples.
Their Hive, Guard messages and results match the page exactly: 150/7 and 100/7, 3 vs 4, 0 vs
3 runs, 6 vs 3 jobs, TEST/SUCCESS vs SUCCESS/FAILED, cache_warm 0, and so on.

**Entries.** None is missing. There are 68 `class="entry"` sections: 7 Worked examples plus 61
docstring entries. Those 61 cover every name in `__all__` (TOOLBOX_VERSION and VERSION share
one entry) plus `example_database.send`.

**Hive vs Python.** All match, including `starts_with`'s `'invoice\\_%'`, which is what
`to_hive` really prints.

**"Computed in pandas" labels.** They appear only where the executor really can't run the
Hive (row_number, NEXT_DAY), which is true.

**Claims that are false or misleading:**

1. **"in the Toolbox": misleading, and pasting breaks.**
   - `examples.html` line 27 says: "Every Worked example in the Toolbox on one page: 7 Worked
     examples on their own…"
   - Each Worked example is labelled "The top of worked_examples/statements/….py" (e.g. line
     59). Regrouping (line 418) and repeated_rows (line 517) import
     `from building_blocks.… import …`.
   - `tools/export_clean.py` ships only `sql_composer/` and `.github/README.md` to the Clean
     branch. So a beginner at work has no `worked_examples/` or `building_blocks/` folder.
   - Following the paste instructions on lines 35-36 therefore fails with
     `ModuleNotFoundError: building_blocks` for regrouping and repeated_rows. The labels point
     at files the reader doesn't have.
2. **The paste instructions miss "today".**
   - Lines 33-36: "The examples take today as 2026-09-25 … To paste one into a notebook,
     first run …"
   - The page never says that a pasted example uses your real today (`conditions.today()` is
     `datetime.date.today()`; only the gallery generator swaps it).
   - So any pasted `last_n_days`/`first_look` example gives different dates in its Hive. From
     2026-09-26 on, it returns no rows from the Example database, with no error.
   - That affects SELECT, JOIN, LEFT_JOIN, WHERE, GROUP_BY, HAVING, ORDER_BY, statement,
     derived, row_number, run, by_day, export_lineage and first_look. The page invites the
     paste and doesn't warn about this.
3. **"any word" vs "every word".**
   - README line 84 says "a box at the top filters the examples by any word". CHANGES line 39
     says "a box filters it by any word".
   - The page's own label (line 38) says "Show only the entries holding every word", and the
     script does AND.
   - "Any word" reads as OR. It isn't strictly false, but it points the wrong way.
4. **The `by_day` snippet throws results away** (not false, but a trap). Lines 1555-1556:
   `for day in by_day(s): df = run(day, send=run_query)`. This overwrites `df` each time, so
   only the last day survives. The same text is in `running.py` `by_day`'s docstring.

## Every stop

Format: file:line, "quote". What I expected / what confused me. **Cost.**

### Cheat sheet (generated from docstring first lines)

1. `clauses.py:332`, "Pair every row with every row of another table; its name is the
   opt-out." Opt-out of what? Only `refusals.py` `guard_cross_join` explains that JOIN without
   ON= is refused and CROSS_JOIN is how you say you mean it. **Reread, then looked it up.**
2. `calculations.py:255`, "descending – Sort by a column from largest to smallest". I looked
   for `ascending` and there is none. I had to guess that a bare column sorts up. **Moment.**
3. `conditions.py:403/412`, "with % and _ matched as themselves". A beginner with little SQL
   doesn't know LIKE's wildcards, so "as themselves" meant nothing until I saw the LIKE in the
   Hive. **Reread.**
4. `refusals.py` group line, "Every Guard, Load limit and Warning in one file, with
   GuardRefused and LoadRefused". A Warning is named, but no Warning class is listed.
   `RepeatedRowsWarning` appears in the gallery (line 565) and can't be imported by name from
   `sql_composer`. **Moment.**
5. `clauses.py:441`, "Sort the result; it needs a LIMIT". Why would sorting need a LIMIT? It's
   answered only in the body. **Moment.**

### Gallery introduction

6. `examples.html:27`, "7 Worked examples on their own, and the 61 examples from the
   docstrings". "On their own" as opposed to what? I had to open CONTEXT.md ("It sits either
   in a Toolbox function's docstring or on its own"). **Reread + glossary lookup.**
7. `examples.html:33-36`: the "today as 2026-09-25" plus paste instructions (bug 2 above). I
   first took it as a fact about the page, then realised my own paste would differ.
   **Stuck** (silent wrong dates).
8. `examples.html:42-43`, "each showing a Statement that gives a wrong number and its fix".
   Fine, but "Careless" as a heading (line 70) needed a moment to map to "wrong". **Moment.**

### Worked example: latest_and_top_n

9. Lines 60-63, the imports. They bring in `all_columns` and `run`, which the shown code never
   uses; they belong to the hidden pandas helpers. I looked for where they were used.
   **Moment.**
10. Line 101, `row_number(PARTITION_BY=…, ORDER_BY=descending(…))`. Capitalised keyword
    arguments, and `ORDER_BY` is also the clause function's name. Do I pass `ORDER_BY(...)`
    here? No, just `descending(...)`. **Reread.**
11. Line 109, `WHERE(equals(numbered.newest_first, 1))`. Why not filter in the same SELECT?
    It's only answered in row_number's docstring (line 1440: "Hive can't filter on a row
    number in the SELECT that makes it"), not here. **Reread.**
12. Lines 169-170: job 3's two runs tie at 30. With row_number, which is "longest"? Both are
    kept only because n=2. **Moment.**

### Worked example: left_join_then_where

13. Line 197, `count_rows(where=is_not_null(job_runs.run_id))`. Why not `count_rows()`? I had
    to work out that LEFT JOIN gives cache_warm one row of NULLs, which `COUNT(*)` would count
    as 1. That is the reason the fix shows 0. Neither the Worked example nor LEFT_JOIN's
    docstring (line 909) says so. **Stuck.**
14. Line 193, "careless(keeps_only_matches=True) pastes the Guard's opt-out". A function that
    "pastes"? It means "passes". The same wording is at lines 455 and 554. **Moment.**
15. `keeps_only_matches=True` as an opt-out name. I had to read it as "I accept that this keeps
    only matches". **Reread.**
16. Line 209, refusal "Usual fix: Move the condition into LEFT_JOIN(job_runs, ON=...), next to
    the join condition". How do I put two conditions in ON=? I had to find `all_of` in fixed()
    (line 231); all_of's docstring then confirms it. **Reread.**

### Worked example: nan_in_a_list

17. Line 255, the title "leaving out the jobs a DataFrame lists leaves out every run".
    **Reread.**
18. Line 285, "item 2 is nan". Is that counted from 0 or 1? The list is `[2.0, nan]`, so it's
    1-based. **Moment.**
19. Line 301, `NOT job_runs.job_id IN (2.0)`. Why 2.0 for a bigint column? The script comment
    on line 269 explains the floats, but the Hive still looks off. **Moment.**

### Worked example: none_in_equals

No stops.

### Worked example: not_equals_drops_null

No stops. It is clear.

### Worked example: regrouping (the one I also ran)

20. Line 418, `from building_blocks.jobs_per_day import jobs_per_day`. What is
    `building_blocks`? It's not in `sql_composer`. I looked up "Building block" in CONTEXT.md,
    then found the folder isn't shipped (bug 1). **Stuck.**
21. Line 463, `GROUP_BY("week")`, a string. The GROUP_BY docstring (line 996) explains it, but
    only if you go there. **Reread.**
22. Line 482, `NEXT_DAY(DATE_ADD(jobs_per_day.dt, 7 * -1), 'MO')`. Why `7 * -1`, and why
    NEXT_DAY? The answer is split between week_start's docstring ("the first Monday after the
    day a week earlier", line 1417, which itself needed a reread) and to_hive's
    ("DATE_SUB(dt, 7) as DATE_ADD(dt, 7 * -1)", line 1502). I worked it through with a
    Wednesday and a Monday to trust it. **Stuck.**
23. Line 469, refusal "Usual fix: Keep the parts it was made from (the sum and the count), add
    those up, and divide after your own GROUP_BY."
    - This fix is for averages. The column is a distinct count, and the real fix, fixed(),
      recounts from the raw rows with `count_distinct`.
    - Line 468 also talks of "a user seen on two days", but this example is about jobs.
    - I tried to apply "the sum and the count" to a distinct count and couldn't. **Stuck.**
24. Line 486, "Result, computed in pandas". How? The helpers
    `every_run`/`with_week`/`careless_in_pandas` aren't shown, so I had to open the script to
    see what was computed. **Reread.**

### Worked example: repeated_rows

25. Line 562, `between(job_runs.dt, DAY, DAY)`, not `equals(job_runs.dt, DAY)`. Why a range of
    one day? I guessed it matches the Building block's (first_day, last_day). **Moment.**
26. Line 590, `LEFT_JOIN(alerts, …)` with no `many_matches` and no Warning. I had to recall
    derived's "Its key is its GROUP_BY columns" (line 1152) to see why it's quiet.
    **Reread.**

### Docstring entries

27. `TOOLBOX_VERSION` (line 630), `'SQL Composer 2.0, ...'`. The `...` is a doctest wildcard,
    which a beginner won't know. **Moment.**
28. `AS` (lines 831 and 837), "Arithmetic uses Python's + - * / and comes out bracketed", yet
    the example shows `job_runs.duration_mins / 60 AS hours` with no brackets. Brackets only
    appear in compound arithmetic: `(job_runs.duration_mins + 1) / 60`, which I checked.
    **Reread.**
29. `CROSS_JOIN` (line 937): the same stop as #1. **Reread.**
30. `JOIN` (line 873), "When ON= doesn't pin down the joined table's whole key". "Pin down"
    needed a reread. The result order on lines 891-899 (95, 99, 101, 104, 96, 98, 102, 97,
    103) looks sorted by team and made me wonder whether JOIN sorts. **Reread.**
31. `JOIN`/`AS`/`SELECT`/`FROM`/`WHERE`/`statement` have no "Worked examples that use it"
    line, though all seven use them. The generator drops names every example uses
    (`tools/example_gallery.py:484`), but the page doesn't say so. **Moment.**
32. `GROUP_BY` (line 1012), "No result here… its executor has no NEXT_DAY". Yet week_start
    (line 1421) and regrouping get pandas results. Why not this one? **Moment.**
33. `INSERT_OVERWRITE` (line 1103), `GROUP_BY(job_runs.dt, job_runs.job_id)`. Why group by dt
    when dt isn't selected and there is only one day? I guessed it's so by_day can split it
    (line 1557). Neither says so. Line 1095 also has "HIVE-18702" and "under Tez", jargon I
    skipped. **Reread.**
34. `statement` (line 1122), "returns_all_rows=True drops the automatic LIMIT, if
    set_load_limits(rows=...) has set one". What automatic LIMIT? Answered only under
    set_load_limits. **Reread.**
35. `is_not_null` (line 1227), `NOT job_runs.status IS NULL`. I expected `IS NOT NULL` and had
    to confirm they mean the same. **Moment.**
36. `equals` (line 1199), `'O\'Brien'` on the status column. It's odd data for a status, but
    the escaping point is clear. **Moment.**
37. `starts_with` (line 1314), `LIKE 'invoice\\_%'`. Why two backslashes? It's one for the
    Hive string and one for LIKE; nothing says so. **Stuck briefly.**
38. `week_start` (line 1417), "takes the first Monday after the day a week earlier".
    **Reread.**
39. `row_number` (line 1440): read well. The derived explanation is clear. Only the
    keyword-argument stop #10 applies.
40. `check_key` (line 705), "20 at most". Twenty what? Keys shown? **Moment.**
41. `run` (lines 1532-1548): the same result appears twice, as "Python shows" and as "Result
    on the Example database". **Moment.**
42. `by_day`:
    - Lines 1555-1556: `s` and `run_query` are undefined, and `df` is overwritten each time
      (bug 4). **Reread.**
    - Lines 1567-1586: two Statements run together under one "Hive" label with no gap, so
      they first looked like one query. **Reread.**
43. `export_lineage`:
    - Line 1647: in "…_1a2b3c4_lineage_weekly_report_runs_per_team.html", is
      "lineage_weekly_report" the file name? `lineage.py` `default_path` shows "lineage" is a
      fixed word. The output on line 1658, `'..._lineage_notebook_runs_per_team.html'`, uses
      "notebook" because the file isn't known. Neither is said. **Reread.**
    - Pasting the example writes files into a `lineage/` folder, and the entry doesn't warn
      you. **Moment.**
44. `Table` (line 637), "`date_partition` is required: … or None". Required but may be None:
    it means you must pass it, even as None. **Moment.**

### README paragraph (`docs/clean-branch-readme.md`)

45. Line 71, "The examples use every Toolbox name". This reads as "each example uses every
    name"; it means "may use any". **Reread.**
46. Lines 81-83, "…the docstrings' examples and the Worked examples on their own, each of
    which shows a Statement that gives a wrong number beside its fix". Does "each of which"
    cover the docstring examples too? Only the second group does. **Reread.**
47. Line 84, "filters the examples by any word": see bug 3. **Moment.**

### CHANGES.md

48. Line 39, "a box filters it by any word": the same as bug 3. Otherwise the line is
    accurate. **Moment.**

## The three costliest stops

1. **The Worked examples reference files a Toolbox user doesn't have.**
   - Where: `examples.html` line 27 "Every Worked example in the Toolbox", the labels "The top
     of worked_examples/statements/….py" (e.g. line 59), and `from building_blocks.…` at lines
     418 and 517.
   - Neither folder ships to the Clean branch, so pasting regrouping or repeated_rows, as lines
     35-36 invite, fails with `ModuleNotFoundError`.
   - "Building block" also needed a glossary lookup.
2. **Pasted docstring examples use your real today** (`examples.html` lines 33-36).
   - The page fixes today at 2026-09-25 but doesn't warn that a pasted `last_n_days`/
     `first_look` example uses the real date.
   - The Hive dates then change, and from 2026-09-26 on the Example database returns nothing,
     with no error. For a beginner, that's worse than a refusal.
3. **Why `count_rows(where=is_not_null(job_runs.run_id))` in the LEFT_JOIN example**
   (`examples.html` line 197, also line 909).
   - The cache_warm 0 depends on it, and nothing explains that `COUNT(*)` would count the
     LEFT JOIN's NULL row as 1.
   - A close fourth is the regrouping refusal's "Usual fix" (line 469; `refusals.py`
     `guard_unsafe_regrouping`). It gives the fix for averages ("the sum and the count") to a
     distinct count, and the example's own fix does something else.
