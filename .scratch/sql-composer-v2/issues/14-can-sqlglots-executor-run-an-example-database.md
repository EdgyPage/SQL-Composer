# Can sqlglot's own executor run an example database?

Type: research
Status: open
Blocked by: -
Findings: branch `research/sqlglot-executor`, file `research/sqlglot-executor.md`

## Question

The example database has to demonstrate the guarantees - show the wrong number a careless
Statement produces beside the right one - and ideally it runs at work, where only stdlib, pandas,
numpy and sqlglot are allowed. sqlglot ships a pure-Python executor
(`sqlglot.executor.execute(sql, schema=, dialect=, tables=)`, confirmed working on 30.18.0 during
charting) that runs SQL over plain Python tables.

Establish, from sqlglot's source, tests and docs:

- which SQL it supports: joins of each kind, `GROUP BY`, `COUNT(DISTINCT ...)`, `CASE`, window
  functions, CTEs, subqueries, date functions;
- whether it accepts Hive-dialect SQL as the Toolbox would emit it, or needs transpiling first;
- whether its results match Hive semantics for the cases the guarantees demonstrate - a join
  that duplicates rows under `SUM`, daily-to-weekly `COUNT(DISTINCT)`, an average of averages;
- how tables are passed (lists of dicts, and whether a pandas DataFrame converts cleanly), and how
  it performs on a few thousand rows;
- documented limitations, and whether it is maintained or a side project within sqlglot.

The findings decide which engine the example database runs on.
