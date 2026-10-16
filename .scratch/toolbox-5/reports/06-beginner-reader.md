# Beginner reader: ticket 06, Windows

Run on commit e00b64a (the first build of ticket 06), on the docstrings of `window`,
`row_number`, `rank`, `dense_rank`, `ntile`, `lag`, `lead`, `first_value`, `last_value` and the
changed ones of `sum_of`, `average_of`, `count_rows`, `min_of`, `max_of`, `descending`,
`hive_function`; the new refusals; how-to 28 ("Look across rows, then finish in pandas") and the
touched lines of how-tos 09, 25, 27, 30; CHANGES.md's window lines; CONTEXT.md's "Window"; and
Lineage's "Rows that count" for a window. Each refusal was triggered in sqlglot Composer and read
in full; how-to 28 was read on its built page. What was done with each stop is in the ticket's
Answer.

23 stops: 3 stuck, 8 rereads, 12 moments.

## The three costliest stops

**1. How to write one day from a Window that looks back across days (stuck).**
`windows.py` window docstring: "To write one day of a Saved table from it, read the earlier
days it needs in a derived(...) table, and keep the day written in the Statement that writes,
with equals(...) of the day the Derived table passes on; run one such Statement for each day."
The by_day refusal sends the reader to help(window) to see how; it only says it, in one sentence
with "it" three times, and the `>>>` example doesn't show it. Only how-to 28's step "Write a day
that looks back on earlier days" made it clear. Leaving out `equals(week.dt, day)` gives
"INSERT_OVERWRITE(run_changes) covers 6 days", whose fix, "for day in by_day(s)", sends the
reader to by_day, which refuses this Statement too. Suggested: say it plainly (read that day and
the days before it in a derived(...) table that keeps the day column; then keep only that day
with WHERE(equals(derived_table.dt, day)) in the Statement that writes), add a short example or
name the how-to, and have guard_one_day_per_write skip the by_day fix for a Window that looks
across days.

**2. `ntile(groups, *, over)`: what "groups" means (stuck for a guess).** Everywhere else a
group is the rows sharing PARTITION_BY values, so `help(ntile)` reads as if its first argument
were those groups; hive_function's refusal calls it `n`. The first line doesn't say what the
value is. Suggested: rename it `parts` (or `n`), first line "Which of N nearly equal parts of its
group each row falls in, 1 to N, in ORDER_BY's order."

**3. row_number's two forms, and its Key sentence (reread several times).** "or, as up to 4.x,
PARTITION_BY= and ORDER_BY= themselves": a first-time reader knows nothing of 4.x and can't tell
which form to use; the example uses only the old one. "Kept at 1, each row is one for each
PARTITION_BY value, which a write's Key check sees" doesn't parse. Suggested: "Give it
PARTITION_BY= and ORDER_BY=, or over=window(...) as lag and rank take: both write the same
Hive." and "Kept at 1, it leaves one row for each PARTITION_BY value, and a write's Key check
knows that."

## Other stops, most costly first

4. window's docstring blames "a lag(...) ordered by the day" for by_day's refusal; the cause is
   a PARTITION_BY that leaves out the day (a lag ordered by run_id is refused too).
5. Lineage puts PARTITION BY under "Rows that count", read as filters; each line says the same
   thing twice ("PARTITION BY of" then "PARTITION_BY="); rows= sits on the ORDER BY line.
   Suggested labels such as "Window of average_of(...), its groups: ...".
6. How-to 28's rank tie example points to job 2's two 18-minute runs, its last, so no gap shows;
   job 1's two 12s (both 3, then 5) do.
7. rank's "doesn't show a Key": suggested "so it can't promise one row per group, as a Key needs;
   keep row_number(...) at 1 for that."
8. "None every row that way": suggested "None means no limit: every row before it when it is the
   start, every row after it when it is the end."
9. The rows= refusal for totals says "It would be unclear which rows" and then says exactly what
   Hive does.
10. The "a total over a Window" regrouping message doesn't say how to keep one row per group, and
    its why fits a group's total, not a running total.
11. A Window in WHERE points to help(window), which has no derived(...) example.
12. `row_number(PARTITION_BY="job_id", ...)` says "Inside a Window, ..." to someone who never
    wrote one, while the ORDER_BY branch says "Inside row_number".
13. How-to 28: "up to a week back" against `timedelta(days=6)`.
14. How-to 28: "its run that day" reads as 2026-09-17.
15. How-to 28: why "each job finishes at most once a day" matters isn't said.
16. How-to 28: the NaN sentence comes after a table that shows NULL, and minutes_before shows
    14.0 with no word on why it is a float.
17. by_day's fix says "the PARTITION_BY of lag(...)", but lag(...) has none; its window(...)
    does.
18. dense_rank's first line means little until the "1, 2, 2, 3" line.
19. first_value and last_value never say what rows= does for them.
20. lag's Hive shows `LAG(..., 1)` though no 1 was passed.
21. `_not_inside`'s why: "a Window inside a function": a Window isn't a value.
22. average_of's over= sentence is wedged into the adds_up paragraph; neither sum_of nor window
    says a total over a Window needs no GROUP_BY.
23. CHANGES.md: "keep the day written with `equals(...)` of the day it passes on": "it" is two
    clauses back.

No stop on: CONTEXT.md "Window", how-tos 25, 27 and 30, the `_whole_number`, swap-rows and
needs-ORDER_BY refusals, the kept-day refusal (apart from the verb "Bound"), `no_window_inside`,
row_number's both-ways refusal, and `descending` and `hive_function`'s new lines.
