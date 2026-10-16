# Beginner reader: ticket 07, Stacks and subtotals

Run on 2026-10-15 on the working copy after the first commit (a1ee296) and the code review's
fixes, sqlglot Composer. The reader read the cheat-sheet lines, every new docstring, both new
how-tos (then 33 and 34, now 35 and 36), each new refusal (triggered live) and the 5.0 CHANGES and CONTEXT lines.
35 stops: 2 stuck, 12 rereads, the rest a moment. How each was handled is in the ticket's
Answer.

## Stops, in reading order

1. `stacking.py` rollup's first line, "each column's total within those before it, and all":
   **stuck**; say what rows you get.
2. is_total's first line, "where the column was added up": a text column isn't added up.
3. grouping_sets' first line, "stacked": that is the Stack word.
4. Module docstring leaves grouping_sets out of its list.
5. "beside each team's and job's row" (and GROUP_BY's "subtotal rows beside the groups"):
   beside reads as a column next to the row; say "as well as" / "added to".
6. UNION_ALL: "so a column is never stacked under one of another name, as Hive, which stacks
   by position, would do": one long sentence, reads as if Hive never does it either.
7. "A column of another type in each": say "a number in one Statement and text in another".
8. "since two Statements may return the same one": the same row or the same Key?
9. "drops the automatic LIMIT": say it is the LIMIT set_load_limits(rows=...) adds.
10. `job_runs` used without being defined in the examples (as in every docstring): a moment.
11. UNION: "keeps one of each set of rows alike in every column...": reread; say "drops repeated
    rows, so each different row comes back once".
12. INTERSECT and EXCEPT: the Key sentence: why care, what "holds" means.
13. EXCEPT's example: say before it what `EXCEPT(alerted, failed)` gives.
14. rollup's Hive: GROUPING SETS looks part of the last column, `()` unexplained, no result
    shown: **stuck** until how-to 34. Name each line of GROUPING SETS.
15. "Columns in GROUP_BY beside it are in every row's group": reread.
16. "A Saved table is never written from subtotals" reads as a fact about Hive: say the
    Toolbox refuses it.
17. cube's example names a count "jobs" beside the table jobs.
18. "[] is one row for all the rows": say grand total.
19. is_total: "there, and in ORDER_BY": what is "there"?
20. The verb "adds up" for a column (about eight places, CONTEXT too): read as summing a text
    column each time; use one phrase such as "totals over".
21. The HAVING/ORDER_BY refusal gives Spark as its reason to a sqlglot Composer user.
22. guard_by_day_stack: "don't all return the Date partition under one name" reads as if it
    were returned under two names; the fix's `AS(run_alerts.dt, "dt")` looks pointless.
23. by_day's fix for a day inside a rollup: say to move it out of rollup(...); the why (partial
    groups, distinct counts) misses that the grand total adds days together.
24. sqlglot Composer can't run any subtotal: the docstrings don't say so beforehand.
25. ORDER_BY/LIMIT inside a Stack, the why: reread. (ORDER_BY without LIMIT is stopped first by
    its Load limit.)
26. Two Derived tables of one name in a Stack, the why: reread.
27. A Stack's Statements reading different days: "make each day's rows together": reread.
28. CONTEXT's Stack lists four kinds without their names.
29. CHANGES: "refused naming the column when a Statement lacks one" (grammar); "UNION_ALL keeps
    every row and loses it" (loses what?); by_day's refusal of a UNION without the day unsaid.
30. How-to 33: "a row one table holds twice and the other once looks the same to it": reread.
31. How-to 33: "what a Saved table's rows should be one per": reread.
32. How-to 34: "every team" sorts between "data" and "finance": a moment.
33. How-to 34: "rollup adds up from the last column back to the first": say it drops columns
    from the right.
34. How-to 34 links "Week and month rollups", which doesn't use rollup(...).
35. How-to 34: "which pandas shows as None", where the page's table shows NULL.

The reader also found the pages older than their sources (both are regenerated after the
fixes).

## The three costliest

1. "Adds up" for a column, about eight places.
2. rollup's cheat-sheet line (stuck).
3. The GROUPING SETS Hive with no result and `()` unexplained (stuck).
