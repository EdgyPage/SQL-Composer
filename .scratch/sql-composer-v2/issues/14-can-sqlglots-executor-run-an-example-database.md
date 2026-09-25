# Can sqlglot's own executor run an example database?

Type: research
Status: resolved
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

## Answer

Yes, with caveats that shape the example database. sqlglot's executor accepts Hive SQL directly
through `dialect="hive"` and handles every join type, `GROUP BY`/`HAVING`, `CASE`, CTEs,
subqueries and `UNION`. Three of the four guarantee demonstrations give careless/correct pairs
that match an independent pandas check: duplicated rows under `SUM` 480 vs 250, an average of
averages 45.0 vs 41.67, and a ratio averaged per day vs recomputed 0.183 vs 0.023.

The caveats:

- **`COUNT(DISTINCT x)` is silently wrong on 30.18.0**: it returns the row count, NULLs included.
  Reproduced independently during resolution: over `a, a, b, NULL` it returns 4, not 2. It is
  fixed in 30.19.0. This affects only the executor; the Hive SQL the Toolbox generates is
  unaffected, and real Hive counts correctly. Without a workaround, the "correct" half of the
  distinct-count demonstration prints a wrong number. The fix is to require sqlglot >= 30.19.0 for
  the example database, or to count through a `SELECT DISTINCT` subquery, which is correct on
  30.18.0.
- **No window functions at all.** A PR adding them was declined upstream, so "latest row per key"
  cannot be demonstrated on the executor.
- **Hive date functions fail** without a roughly 40-line add-on. Simpler: store week and month
  buckets as plain columns in the example tables.
- **Loading.** Tables go in as lists of dicts. A DataFrame needs `df.to_dict('records')` with NaN
  converted to None first. An empty table needs an explicit `schema`, because types are inferred
  from the first row.
- **Speed and age.** A join plus `GROUP BY` over 5,000 rows takes about 185 ms. Outer-join and NULL
  handling were fixed in 30.15.0, so anything older is worse.
- **Maintenance.** 17 commits touched the executor between July and September 2026, but the core
  team calls new executor features "not a priority".

Not verified: nothing ran on real Hive; "matches Hive" rests on Hive's documented aggregate,
division and NULL behaviour plus the pandas cross-check. 30.19.0 was not installed; the fix was
confirmed by applying its diff to a scratch copy. Hive rounds halves up and the executor's `ROUND`
may not; that was read from the code, not run.

Findings: branch `research/sqlglot-executor` (commit `2878e67`), file
`research/sqlglot-executor.md`, with rerunnable probes under `research/sqlglot-executor/`.
