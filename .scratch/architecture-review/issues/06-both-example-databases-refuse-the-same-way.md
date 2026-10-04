# Both Example databases refuse the same way

Type: task
Status: claimed
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
