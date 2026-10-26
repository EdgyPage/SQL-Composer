# Beginner reader: Toolbox 7.2 ticket 10, every row of the conversion chart

Read 2026-10-26 on 031d36a: the Worked example latest_and_top_n run on the Example database
(careless, fixed and top_runs_per_job, their Hive and rows), the new window refusals from raw
Hive and through Toolbox calls, and compare_hive and compare_with_original with `*`, `r.*` and a
query in brackets. Saved by the session (the reader writes no file).

## Stops

1. compare_hive, a query in brackets matches only when the name after the bracket is the
   Derived table's; the Verdict then shows a WITH the original lacks. (stuck, until run)
2. "where they can be told": told means worked out, and nothing says what happens when they
   can't be. (a reread)
3. "by its Table reference": nothing public says a * gives the partition columns last.
   (a reread)
4. compare_with_original, a * over a table it doesn't read: "as its columns can't be" what?
   The refusal's fix says a * "needs a name too", and never the real reason. (a reread)
5. The RANGE refusal, "has no a window whose RANGE ...": broken grammar, and window() offers
   only rows=. (a reread)
6. "has no the window function PERCENT_RANK": broken grammar, and no list of those it runs.
   (a moment)
7. "has no windows outside SELECT's columns": where else can one go, and how to keep the order?
   (a reread)
8. Every window refusal's fix points at the Statement, where the part came from the original
   given to compare_with_original. (stuck)
9. How-to 13's page: "Python shows" above a paragraph saying the Example database can't run
   row_number and the result came from pandas (drift D283). (stuck)
10. How-to 10's numbering table counts down, as its rows come by event id; nothing says so.
    (a moment)
11. How-to 17's change column shows 1.0, then 1. (a moment)
12. latest_and_top_n's top N comes back by run, not longest first. (a moment)
13. The gallery's window entry: the label of Statement 1's result sits below Statement 2's
    Hive. (a moment)
14. CHANGES, "NULL first in an ascending order": in what? (a moment)
15. CHANGES, "adds rows up after any join" read as "adds rows"; "where it stopped". (a reread)
16. CHANGES names how-to 10 short of its title, and leaves out how-to 13. (a moment)

## The three costliest

Stop 8, stop 1, stop 9.
