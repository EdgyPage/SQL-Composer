# Ticket 02: the beginner reader on by_day's refusals (2026-10-03)

The beginner reader read the working tree's diff and ran each refusal from the scratchpad. All
six messages were four-part. It stopped 9 times. Each stop, and what was changed:

1. refusals.py's "a grouping or a LIMIT by_day can't split" read as one noun, and hinted that
   some LIMITs split. **Changed:** "by_day stops at any LIMIT and at a grouping it can't split".
2. The LIMIT Guard's "each day would keep its own": its own what? And "the outer Statement"
   for a Statement with no Derived table. **Changed:** "each day would keep 10 rows of its
   own, not the 10 you asked for"; a Statement with no Derived table is called "it" ("by_day
   can't split this Statement: it has LIMIT 10"), since "your Statement" repeated the line's
   start.
3. "If it reads too many days for that": too many for what? **Changed:** "If
   set_load_limits(dates=...) refuses it, read fewer days."
4. by_day on jobs: "Put a table with a Date partition in FROM" changes the question.
   **Changed:** "Run it whole with run(...): by_day splits only a table with days." A write
   keeps its own fix: a Saved table is filled from a table with days.
5. by_day after `reads_all_partitions=True` said "nothing bounds the days", which felt like it
   ignored the opt-out. **Changed:** "FROM(job_runs, reads_all_partitions=True) reads every day
   of ops.job_runs, so there are no days to go by".
6. A write's "the day to write isn't known: its FROM table..." had two colons, and "the one day
   its FROM table is read for" was hard. **Changed:** "INSERT_OVERWRITE(...) can't tell which
   day to write: ..."; "A write fills the one day its FROM table reads."
7. The dates cap's "in its own bound": "bound" isn't in CONTEXT.md. **Changed:** "Narrow the
   between(...) or last_n_days(...) on ops.run_alerts's Date partition, in WHERE or ON=, to 1
   or fewer days. by_day won't help: it splits only the days of the table in FROM."
8. CHANGES' "## Not yet numbered": is it in my version? **Not changed:** the heading exists
   only on the Dev branch; an export refuses while the version item is open, and the user names
   the version before it ships, as with 3.2.
9. CHANGES' by_day lines: "took ... as", "partial groups" and "at any step". **Changed:** "It
   checked only the name dt, so grouping by any column called dt passed, and each day got part
   of a total"; "in your Statement or in any Derived table".
