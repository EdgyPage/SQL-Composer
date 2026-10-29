# File 11 reaches the clauses Excel has a clean source for

Type: task
Status: claimed
Blocked by: 18
Size: M

## Question

The user asked (2026-10-29) "Are all supported SQL clauses accounted for?" Every Clause function
is named in the Copilot files, but file 11 turns a workbook into only some of them: SELECT,
FROM, WHERE, GROUP BY, LEFT JOIN and JOIN, ORDER BY with LIMIT, UNION ALL, SELECT DISTINCT, a
window and CTEs. Excel or Power Query has a clean source for more, which file 11 left out, so
Copilot would refuse or guess:

| Excel or Power Query | Hive |
|---|---|
| Table.SelectRows on a Table.Group | HAVING |
| JoinKind.RightOuter, FullOuter, LeftAnti | RIGHT JOIN, FULL OUTER JOIN, the anti join as ANTI_JOIN writes it |
| Table.Combine, then Table.Distinct | UNION |
| RANK.EQ | RANK() OVER |
| MINIFS | MIN, as MAXIFS is MAX |
| SUMIF, COUNTIF, AVERAGEIF | as the -IFS forms, with one match |

And four mappings file 11 already names were never tested: JoinKind.Inner, Table.Distinct,
List.Min and List.Average.

The user: "Yes, extend it": to the first group, with eval tasks for those and for the four
untested mappings. INTERSECT, EXCEPT, CROSS JOIN and SEMI JOIN have no natural Excel source and
stay out; INSERT is file 06's.

## Done when

- New tasks in `tools/excel_eval_tasks.py`, written and committed before file 11 changes, so the
  held-out ones are unseen: 5 dev (X41 to X45) and 5 held out (X46 to X50), each new kind in
  each split, and combinations of them.
- File 11 maps each, at most 8,000 characters in both counts, trimmed elsewhere to fit.
- At most two tuning rounds on dev, Haiku, arm C; then one held-out round on the final files,
  Haiku and Sonnet, arms A0 and C, on the whole held-out split, meeting ticket 18's thresholds.
- `.venv/Scripts/python -m pytest` passes; the code review, the beginner reader on file 11, and
  the drift review are clean; CI passes; exported to main again.

## Answer
