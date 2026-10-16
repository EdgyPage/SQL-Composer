# Beginner reader: ticket 08 (upkeep and speed)

Run on the change since 5b82ba1, read as a sqlglot Composer user: `repair_partitions`,
`compute_statistics` and `explain` (composer_core/upkeep.py), `need_saved_table`
(composer_core/tables.py), the changed paragraphs of `create_table`, `hive_settings` and `run`,
how-to 33 "Keep reads and joins fast", the 5.0 lines of CHANGES.md and CONTEXT.md's Statistics
and Plan. Every `>>>` step of the how-to's sqlglot path was run and gave what it shows; each
refusal was called. Line numbers are as of commit 6fe73e1. What was done with each stop is in
the ticket's Answer.

## Stops, in reading order

### Cheat sheet

1. upkeep.py:37, "The MSCK REPAIR TABLE Statement, which finds the days in a Saved table's
   folder." "Finds" doesn't say it adds them to the list the warehouse reads; "MSCK" means
   nothing. A moment.
2. upkeep.py:68, "The ANALYZE TABLE Statement, counting a Saved table's day for Hive's
   planner." Counting what? "Hive's planner" isn't a glossary word, though Plan is. A reread.
3. explain's first line: clear.

### repair_partitions

4. upkeep.py:41-42, "since it was dropped without purge=True": read "since" as "from the time
   when", not "because". A reread.
5. upkeep.py:45-46, "The Example database can't run it": its refusal says "it can't be
   written to", a different reason from the docstring's ("deletes no file"), and lists what
   to_hive takes without the three new functions. A moment.

### compute_statistics

6. upkeep.py:71-73, "where copying a small one to every worker would do" ("where" for
   "whereas"; the same in explain and the how-to), and "that choice". A reread.
7. upkeep.py:75-76, "this is for the days written without it": two pronouns. A reread.
8. upkeep.py:80, "A Saved table with no Date partition takes no day": no example; Table needs
   date_partition=None given. A reread and a trip to help(Table).
9. upkeep.py:84-85, Spark counts columns over every day: a cost warning with no advice (the
   how-to's "name only those few" is it). A reread.
10. upkeep.py:94, why dt is missing from FOR COLUMNS (line 81 says). A moment.
11. upkeep.py:157-160: `columns=[daily_runs.job_id]`, as columns are written everywhere else,
    is refused as "daily_runs.job_id isn't one of its columns", then "Use some of: job_id,
    runs". Stuck for a while: accept the column, or say to write its name as text.
12. The badly written day's refusal (tables.py:390-395 through upkeep.py:127) says
    compute_statistics "compares the Date partition" and suggests last_n_days, which it
    doesn't take. A reread.

### explain

13. upkeep.py:178-190, one 12-line paragraph mixing what it does, how to read a plan, what it
    takes and the Example database; "the automatic LIMIT too" isn't explained; "only where it
    runs on Spark" doesn't tell a sqlglot Composer reader that theirs gives none. The
    executor's "try the Statement here without that part" took a second. A reread, the
    longest.
14. upkeep.py:191, the example uses job_runs, which the star import doesn't define (as in
    run's docstring). A moment.

### Elsewhere

15. create_table, may_exist=True: clear; a pause on whether it refuses a mismatch. A moment.
16. hive_settings: clear.
17. run: clear.
18. need_saved_table's refusal: clear; "changes the table, or what the warehouse keeps about
    it" slightly odd for compute_statistics, but the "or" covers it.

### How-to 33

19. Line 10, "keep a Saved table's list of days true": Python's True for a second. A moment.
20. Line 40, "as the Load limits insist": known from how-to 15. A moment.
21. Lines 96-98: map_joins is only printed, where the settings two steps earlier were run.
    A moment.
22. Lines 103-104, "`JOIN(jobs, ON=..., broadcast=True)` asks it by name...": JOIN has no
    broadcast= in either Edition (ticket 05, still open); TypeError. Stuck.
23. Lines 150-164, the Edition-only markers in the raw file. A moment.
24. Lines 193-195, "should say COMPLETE": the after state is never shown in full. A moment.
25. Lines 217-218, "leaving the day out would read the whole table": holds only for a table
    with a Date partition. A moment.

### CHANGES.md and CONTEXT.md

26. CHANGES.md:65-75, one ten-line sentence ending "is the fourth": the fourth what? A reread.
27. CONTEXT.md Statistics, "which it picks how to join the table from": word order; Plan says
    "the warehouse" where the docstrings say "Hive's plan". A reread.

## The three costliest

1. How-to 33, line 103, `JOIN(..., broadcast=True)`: no such argument yet; stuck.
2. upkeep.py:157-160, a column attribute in columns= refused as not a column; stuck for a
   while.
3. upkeep.py:178-190, explain's one long paragraph; a reread.
