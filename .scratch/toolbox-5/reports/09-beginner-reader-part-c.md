# Beginner reader: ticket 09 Part C (a Saved table with no days, written whole)

Run on commit 847fc1d, sqlglot Composer. Read: INSERT_OVERWRITE's and INSERT_INTO's
docstrings, Table's date_partition bullet, how-to 10's "A table with no days, written whole",
CHANGES 5.0's entry, the README's sentence, and the refusals of by_day and admin.drop_days
(run). Every example built or refused as the docs say. It edited nothing.

## Stops

1. clauses.py 866, INSERT_OVERWRITE's first line, "replacing one day, or all of it": "all of
   it" read as all of the day. A reread.
2. clauses.py 868-869 against 896-900: the first paragraph states the one-day rule and by_day
   with no exception; the exception comes three paragraphs later. A reread.
3. clauses.py 897-898, "may read several days ... each bounded as any read is": never shown;
   both examples read ops.jobs, which has no days. Stuck until running a guess.
4. The example's `SELECT_DISTINCT(jobs.job_id, jobs.team)` (docstring and how-to): it looks like
   what proves the Key, but DISTINCT over both columns doesn't make one row per job_id; jobs'
   own Key does. Teaches the wrong reason. Stuck.
5. clauses.py 943, INSERT_INTO's first line still says "a day". A moment.
6. tables.py 578-581: clear; "days" vs the glossary's Date partition. A moment.
7. How-to 10, 406-407, "Its Hive has no PARTITIONED BY": the section shows only the write's
   Hive, not create_table's. A moment.
8. How-to 10, 415: `purge=True` here but not in the docstring's same table. A moment.
9. How-to 10, 429-431, "writes them all at once": the days? A reread.
10. How-to 10, 482-485, Common mistake "A write fills one day": a flat rule the new section
    just made an exception to. A reread.
11. CHANGES 82-84, "by_day refuses such a write ... and so do admin.drop_days and
    repair_partitions": they take a table, not a write, refuse for another reason, and refused
    before 5.0 too. A reread.
12. The by_day refusal of an INSERT_INTO write explains it with INSERT_OVERWRITE replacing the
    day before, which doesn't fit INSERT_INTO; "from every day it reads" odd for a read of
    ops.jobs. A reread.
13. admin.drop_days' refusal names the table `t` where repair_partitions' names the variable;
    the four-step "to empty the table" is heavy. A moment.
14. README 250-252: the section's last paragraph offers only day-level tools for a section
    that now opens with tables with no days. A moment.

## The three costliest

1. Stop 4: the example's SELECT_DISTINCT isn't what proves the Key.
2. Stop 3: reading several days, the one new thing, has no example.
3. Stops 2 and 10: flat one-day rules the new passage reverses.
