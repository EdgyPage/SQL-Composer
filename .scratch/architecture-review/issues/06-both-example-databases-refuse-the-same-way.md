# Both Example databases refuse the same way

Type: task
Status: resolved
Blocked by: 05

## Question

`engine.run_query` is the seam between the shared Example database and each Edition's way of
running a query, and it has two adapters (candidate 6 of [report.html](../report.html)).
Spark Composer's refuses a query it can't run in four parts, naming the tables; SQL Composer's
doesn't, and only Spark Composer's tests check it:

1. **A misspelt column or table** reaches the user as sqlglot's own `OptimizeError`
   ("Column 'nope' could not be resolved") from SQL Composer's Example database.
2. **An executor error that isn't a missing function** comes out as "its executor has no what
   this needs (...)", with sqlglot's text inside it.
3. **`DESCRIBE mart.jobs`** is answered as if it were `ops.jobs`, though a SELECT from
   `mart.jobs` is refused: the shared `_table` matches a table by its short name only.
4. **`example_database.send(5)`**, or a Statement passed straight to it, leaks an
   AttributeError.
5. **`_executor_ready`** repeats `example_database_cannot_run`'s version check, and its Usual
   fix says what still works, not how to fix it.

## Decisions (the user asked for this candidate on 2026-10-03; the rest are the agent's)

- **SQL Composer's adapter refuses what sqlglot can't read or run in four parts**, as Spark
  Composer's does: what sqlglot said, that a name spelt wrong is the usual cause, and the
  tables to choose from. An executor error that names no function gets that refusal too.
- **The shared Example database refuses a table in another database** for DESCRIBE and SHOW
  PARTITIONS, in the words a missing table already gets, and **refuses anything but Hive text
  in `send`**, pointing to run(s, send=...) and to_hive(s).
- **`_executor_ready` asks `example_database_cannot_run`**, and its fix says which sqlglot to
  install.
- **A shared test holds the contract**: a misspelt column is refused in four parts naming
  `example_database.jobs`, in both Editions.
- **Out of scope:** passing full table names across the seam. The database name `ops` is in
  Spark Composer's helper process anyway, where its Spark is told to use it.

## Done when

- Each of 1-5 has a test, the contract in both Editions; every new refusal is four-part.
- Both runs pass; goldens and galleries regenerated if their text changed.
- The code-review skill has run with this ticket as its spec, the drift items are closed, and
  the beginner reader has read the new refusal text.

## Answer

Built in `d25dc00`, reworked after the review in `3ac76f2`.

- SQL Composer's run_query refuses what sqlglot can't read or run in four parts
  (`_refuse_unreadable`), as Spark Composer's refuses what Spark can't: what sqlglot said,
  without where it stopped, that a table, column or hive_function(...) name spelt wrong is the
  usual cause, and the tables. It checks each table in the query sqlglot has read
  (`_check_tables`), so a table outside ops is refused for the table, not for a column.
  `_cant_run` is `_refuse_missing_part`, so the two refusals' names say which is which.
- The shared Example database refuses a table outside ops for DESCRIBE and SHOW PARTITIONS,
  and anything but Hive text in send.
- `_executor_ready` asks `example_database_cannot_run`, and says what to install; when the
  version is new enough but the count is still wrong, it says that, not that the version is
  too old.
- `tests/test_example_database.py` holds the contract in both Editions: a misspelt column, a
  table outside ops (after a comma too), a missing table and a parse error are each refused
  in four parts naming example_database.jobs.

**Beginner reader** ([report](../reports/06-beginner-reader.md)): 7 stops; 6 changed, 1
answered.

**Code review (2026-10-03), `d25dc00`.**
- *Standards:* no hard violations. Fixed: hive_function(...) among the names to check, as in
  Spark Composer's refusal; send's fix for a non-Statement; `_executor_ready`'s message when the
  version isn't the trouble; plainer names for the two refusals. Kept: each engine lists the
  tables in its own words, since each is hand-written.
- *Spec:* the table check first added to the shared code matched FROM inside EXTRACT(...) and
  TRIM(...), and in a block comment, and refused queries both Editions can run; it is gone,
  and SQL Composer's adapter reads the tables from sqlglot's tree instead, a table after a
  comma included. sqlglot's "Line 1, Col: 45." is now left out too. The SELECT-time refusal of
  a table outside ops is recorded here: it came from the beginner reader, and both Editions
  give it as the four-part RuntimeError Spark Composer's Spark already gave.

| Items | Opened by | Closed by |
|---|---|---|
| (none) | `d25dc00` was clean | |
