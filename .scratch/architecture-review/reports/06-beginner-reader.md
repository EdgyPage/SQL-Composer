# Ticket 06: the beginner reader on the Example database's refusals (2026-10-03)

The beginner reader ran four calls on SQL Composer's Example database and read Spark Composer's
`_refused`, which it couldn't run without Java. Each refusal was four-part. It stopped 7 times:

1. `SELECT job_id FROM mart.jobs` blamed the column ("Column 'job_id' could not be resolved"),
   though the database is what's wrong, while DESCRIBE mart.jobs named the table.
   **Changed:** the shared Example database checks each table a query names with its
   database, after FROM or JOIN and in backticks too, before it runs, so both Editions refuse
   `mart.jobs` and `ops.nope` for the table.
2. "Or it is a part of Hive the Example database's small executor doesn't know, which your
   warehouse does." **Changed:** "Or the Hive uses a part of Hive your warehouse knows but the
   Example database's small executor doesn't."
3. sqlglot's "Line: 1, Col: 11." broke into the sentence. **Changed:** it is left out.
4. "It holds only three made-up tables", though it does hold a jobs. **Changed:** "It holds
   three made-up tables, all in the database ops."
5. CHANGES' quoted "its executor has no what this needs" read like a typo in the notes.
   **Changed:** "gave a garbled message (\"... has no what this needs\")".
6. CHANGES' "Too old a sqlglot ... is told which to install". **Changed:** "With too old a
   sqlglot, the Example database's refusal says which version to install."
7. The refusals are three error types: RuntimeError, ValueError and TypeError. **Not changed:**
   a query the warehouse can't run is a RuntimeError in both Editions, a table it hasn't got a
   ValueError, and a send given something other than text a TypeError, as across the Toolbox.
