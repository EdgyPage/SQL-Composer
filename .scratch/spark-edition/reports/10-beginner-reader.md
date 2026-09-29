## Beginner-reader report, ticket 10 (the Example database's row order; CHANGES 2.1)

Read-only; the reader changed nothing.

Files: `sql_composer/example_database.py` (lines 1-21), `sql_composer/CHANGES.md` (lines 46-47).

What the reader saw when they ran it: without ORDER_BY, the 2026-09-24 rows came back in run_id
order (101-104). With `ORDER_BY(descending(runs.duration_mins))` plus `LIMIT(10)` they came back
104, 103, 102, 101. So the sorting works the way the text says.

### Stops

1. **example_database.py:7-8, "gets them sorted by every column".** The reader expected one sort
   key and got "every column", which left them asking which column comes first. The docstring
   example starts with run_id, so it looks like a sort by run_id. They had to run
   `SELECT(runs.status, runs.run_id)` to learn that the sort goes left to right in SELECT order,
   with None first. "NULL first" is only in the private `_in_order`. **Reread plus an experiment.**
2. **The write refusal, "Usual fix: A write's Hive can still be shown with to_hive(...)."** The
   reader had sent a plain string, so they tried `to_hive("DROP TABLE ops.jobs")`. That was
   refused, and the refusal told them to "Pass statement(SELECT(...), FROM(...), ...)", which has
   nothing to do with dropping a table. They only got out because they remembered `drop_table(t)`
   from CHANGES.md:11. The fix doesn't mention `drop_table` or say that to_hive needs a
   Statement. **Stuck.**
3. **example_database.py:5 and 7-8.** Line 5 says the send is "just like your own send at work",
   and then the new sentence says the rows come back sorted. The first reading was that the send
   at work sorts too. Nothing says that real Hive gives no fixed order without ORDER BY, so a
   beginner could come to rely on the order at work. "so every run shows them in the same order"
   also doesn't say why the order would ever change. **Reread.**
4. **example_database.py:8, "every run".** The example just before names
   `runs = example_database.job_runs`, so for a second "run" read as a job run and not as a call
   to `run(...)`. **A moment.**
5. **ORDER_BY as the way to pick an order.** The sentence makes it sound like that, so the reader
   tried a bare `ORDER_BY(...)`. It was refused ("ORDER_BY has no LIMIT"). The refusal was clear,
   but neither the new sentence nor the CHANGES bullet warns about this. The refusal's "sort in
   pandas" advice also left them unsure whether to rely on the database's sort or on pandas.
   **A moment.**
6. **Different words in the two texts.** The docstring says "A query" with a bare ORDER_BY.
   CHANGES says "its Statement" with `ORDER_BY` in backticks. The reader stopped to check whether
   a query and a Statement are the same thing here. **A moment.**
7. **example_database.py:4-7, "sqlglot's own executor" and "It needs sqlglot 30.19.0 or
   newer".** This text was already there before the ticket. The reader didn't know what sqlglot
   or an executor is, and had to look up which sqlglot version they have (30.19.0). **A moment.**

No trouble: the refusal's "What happened" and "Why it matters" lines, and the rest of the
CHANGES bullet.

### The three costliest stops

1. The write refusal's fix sends someone holding a plain string to `to_hive(...)`, which refuses
   strings and points at `statement(SELECT...)`. It never names `drop_table`. (Stop 2)
2. "sorted by every column" doesn't say which column counts first or where None goes. The reader
   only found out by running a query. (Stop 1)
3. "just like your own send at work" followed by the sort sentence makes it sound as if the order
   is fixed at work too. Nothing says real Hive has no fixed order without ORDER BY. (Stop 3)
