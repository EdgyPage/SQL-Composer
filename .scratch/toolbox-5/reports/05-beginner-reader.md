# Beginner reader: ticket 05, Joins

Run on the uncommitted work against e82a55a (sqlglot Composer), before the fixes listed in
the ticket's Answer. The reader edited nothing.

## The three costliest stops, most costly first

1. **The semi-join result in how-to 33 can't be reproduced in sqlglot Composer** (how-to
   lines 81-92 and 295-298). Stuck. The page shows `run(with_an_alert, ...)` with rows; typed
   in, it raises `RuntimeError ... its executor has no LEFT SEMI JOIN`. The note only says
   "the result above is worked out in pandas", where earlier how-tos say plainly "Pasted into
   your own notebook, this `run` stops with a RuntimeError...". "Check it worked" runs
   `len(run(with_an_alert, ...))`, which raises too, with no warning.
2. **broadcast=True is ignored by Hive unless a setting the Toolbox never shows is changed**
   (JOIN's docstring, how-to, CHANGES). Stuck. Why is it there, then? "map_joins" sets only
   hive.auto.convert.join*; nothing says to set hive.ignore.mapjoin.hint=false through
   `hive_settings(..., sets={...})`. `/*+ ... */` looks like a comment. "Spark always follows
   it" made the reader wonder whether their warehouse is Spark.
3. **FULL_JOIN's opt-out `keeps_only_matches=True` doesn't keep only matches.** With
   `WHERE(more_than(recorded.run_id, 96))` it returned run 99 with started NaN: an unmatched
   row. Neither the docstring nor the refusal says what rows you get once you opt out.

## Every stop, in reading order

### Cheat sheet (first lines)
- SEMI_JOIN: "adding none of its columns": the row's or the other table's? A moment.
- FULL_JOIN: "keep each table's rows with none": "with none" means no match. A moment.
- RIGHT_JOIN: a cheat-sheet entry that only refuses; "the same rows" as what? A moment.
- How-to line 10 says "see why there is no `RIGHT_JOIN`", yet it is a public name. A moment.

### Docstrings
- JOIN broadcast: "worker" isn't defined. A moment.
- Which joins take broadcast=? JOIN's paragraph doesn't say; FULL_JOIN(..., broadcast=True)
  gives a bare TypeError. Found only in CHANGES and the how-to. A moment.
- SEMI_JOIN: "written LEFT SEMI JOIN": why LEFT? A moment.
- ANTI_JOIN: which column is tested for NULL, and why that finds the unmatched rows. A reread.
- ANTI_JOIN: "It never repeats rows": a LEFT JOIN repeats rows when several match. A reread.
- FULL_JOIN: "unless it is is_null(...)": is any_of(...) of them allowed? Only the example
  says. A moment.
- FULL_JOIN: "a bound in ON= would keep every day's rows all the same" is dense. A reread.
- FULL_JOIN: "a write needs a GROUP_BY over the Key": which Key? The how-to gives no example;
  `GROUP_BY(AS(fill_null(...), "run_id"))` was refused, `GROUP_BY(fill_null(...))` worked.
  A reread and a wrong guess.
- FULL_JOIN: "many_matches= is as JOIN's." A moment.
- FULL_JOIN example: `AS(started.run_id, "started")` names a column like the Derived table.
  A moment.

### Refusal messages
- ANTI_JOIN with nothing matched: "a column ON= sets equal to something" misread. A reread.
- ANTI_JOIN column read in WHERE: "every run_alerts column is NULL in them" doesn't say what
  goes wrong. A moment.
- sqlglot's "its executor has no LEFT SEMI JOIN": "try the Statement here without that part"
  doesn't say what to write instead, nor that Spark Composer runs it. A moment.
- The others read cleanly on the first try.

### Lineage and Keys
- "ANTI JOIN ON (keeps the rows with no match)" beside Hive that has only a LEFT JOIN and a
  WHERE ... IS NULL the reader never wrote, with no box for the IS NULL. A moment.
- The FULL_JOIN Keys reason was clear.

### How-to 33
- Line 120: an IS NULL the reader didn't write, chained onto a BETWEEN. A reread.
- Lines 158-160: which side loses what with a bound in WHERE or ON=. A reread.
- Lines 243-244: the GROUP_BY advice without an example.
- Lines 276-281: top stop 2.

### CHANGES.md, Example database, CONTEXT.md
- CHANGES: "is refused (opt-out ...), so each side's days are bounded in a Derived table":
  "so" reads as if the refusal causes the bounding. A reread.
- Example database docstring: three tables, then scheduler_runs, then "Three more": had to
  count to seven; "These three ... don't match job_runs run for run" sits next to
  scheduler_runs, which should. A reread.
- CONTEXT "Map join": the keyword is `broadcast=`; why not `map_join=True`? A moment.

## Aside
sqlglot_composer/how_to.html lagged the .py source at the time of reading (regenerated since).
