# Spark Composer is dropped; sqlglot Composer is the one Toolbox

Status: accepted; supersedes ADR 0002

From 6.0 the Toolbox is built once, as sqlglot Composer. ADR 0002 built it twice because it wasn't
settled whether the warehouse at work would run Statements on Hive or on Spark. It is settled
now: the warehouse is Hive 3 (Toolbox 5.0's map), and the user develops and maintains only
sqlglot Composer. Every feature since 3.0 has cost two writers, two Example databases, a golden
corpus each and a parity test between them, and Spark Composer's Example database needed Java 17
and a second Python. That cost bought nothing the user runs.

So on `dev`, Spark Composer, its tests, its CI jobs, its requirements and the machinery that held
the two Editions alike (`DECLARED_DIFFERENCES`, the name swap, `--edition`) are removed. The
offline trap Spark Composer's Example database ran under, which every test run installs too,
moves into `tests/offline_trap.py`, with its reviewed entry in `tools/offline_policy.py`.
`main` ships sqlglot Composer alone from 6.0.

Nothing is lost for good: the tag `last-spark-composer` marks the last `dev` commit with both
Editions, and `main`'s commit `e60445c` (5.1) is the last export of both.

A notebook whose `send` runs the Hive on Spark (`spark.sql(hive).toPandas()`) still works with
sqlglot Composer, but gets Hive's text, not Spark Composer's adjusted Hive: a division by 0 stops
a query under Spark's ANSI mode, a float is read as a DECIMAL, and `create_table`'s
`PRIMARY KEY ... DISABLE NOVALIDATE` is refused. The README says so.

## Considered options

- **Keep Spark Composer on `dev`, unexported.** Rejected: it would still cost every change its
  parity, and git keeps it anyway.
- **Freeze Spark Composer at 5.1 on `main` beside 6.0.** Rejected: two versions on one branch,
  one of them never updated, would mislead whoever copies it.
