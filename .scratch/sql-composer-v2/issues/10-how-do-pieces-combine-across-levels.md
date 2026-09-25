# How do pieces combine across Levels - CTE, subquery, or saved table?

Type: grilling
Status: resolved
Blocked by: 01
Findings: branch `research/hive-writes-and-ctes` (commit `78a5136`), file `research/hive-writes-and-ctes.md`

## Question

When a Statement uses a Building block, the block can land in the final string as a CTE, as an
inline subquery, or as a separately written table that the Statement then reads.

A CTE keeps everything in one string, which sqlglot can trace directly, but Hive may recompute a
CTE that is referenced twice. A saved table is computed once, but it needs its own write
statement and a place to live, and its lineage has to be stitched across the boundary.

Decide the default, when (if ever) to save a table instead, and how a saved table's lineage links
back to its sources.

## Comments

**From "How does a composed Statement read?"** A sub-query Building block returns a named
Statement, `derived("latest", statement(...))`, whose output columns are checked attributes. The
prototype (branch `prototype/statement-styles`) tried two ways of placing it: an explicit
`WITH(latest)` clause, and a derived table inlined as a sub-query when `WITH` doesn't name it. A
third variant, where the Toolbox adds the `WITH` automatically, was tried in the ruled-out pandas
style. This ticket picks among them.

**From "How much may a Statement touch and return by default?" (2026-09-25).** The query API can
write tables, and one call carries one full SQL string. Backfills are a loop over `by_day(s)`,
which returns one single-day Statement per date. Each pass sends a write, so a saved table's write
statement must accept a single-day Statement and write only that day's partition. What that write
looks like (`INSERT OVERWRITE ... PARTITION`, `CREATE TABLE AS`) is decided here. An automatic
`LIMIT`, if it's ever turned on, never applies to a write.

## Answer

**A Derived table always lands as a CTE the Toolbox writes. A Saved table is always something the
user writes explicitly, and it is read back like any other table.**

**Derived tables, inside one string:**

- **The Toolbox writes the `WITH`.** Every Derived table a Statement reads (through `FROM`, `JOIN`
  or another Derived table) becomes `WITH latest AS (...)` at the top of the string, ordered so each
  comes after the ones it reads. There is no `WITH(...)` clause, and nothing is ever inlined as a
  sub-query, so one Statement has one string shape. Two different Derived tables with the same name
  refuse at `statement(...)`, as a plain error rather than a Guard.
- **A reusable CTE is a Derived table kept in a Building block.** The user keeps `latest =
  derived("latest", statement(...))` in a Level 1 `.py` file, and several Statements import it. It
  reads like any table (`latest.status` is checked), each Statement gets its own copy in its own
  `WITH`, and lineage traces straight through it. "Save" is kept to mean writing to the server.
- **One Derived table used twice is allowed silently.** Hive 2.3 to 4.0 compute a CTE read twice
  twice (from 4.1 it is reused automatically, and Tez on 3.1+ may merge the scans), and one query
  string can't carry a `SET` to change that. The answer is still right and the date bound still
  limits each read, so it is neither a Guard nor a Load limit. `derived`'s docstring says it is
  computed once per use and suggests a Saved table when that gets expensive.
- **`by_day` follows `FROM` down through Derived tables** to the real table and narrows that
  table's date bound. It refuses, with no opt-out, if any level along the way aggregates or picks
  rows (latest per key, `GROUP_BY`, `DISTINCT`) without keeping the date in its grouping, and the
  message names the Derived table that broke the rule. It is the same rule "How much may a
  Statement touch and return by default?" set for the outer Statement. Joined tables keep their own
  bound.

**Saved tables, across strings:**

- **Saving is explicit.** The Toolbox never saves a table on its own. A Saved table is written by a
  Statement and read back by other Statements through its own Level 0 Table reference, like any
  other table.
- **A write is a Statement whose first clause is `INSERT_OVERWRITE(table_ref)`:**

  ```python
  fill = statement(
      INSERT_OVERWRITE(daily_failures),        # the Saved table's Table reference
      SELECT(runs.region, AS(count_rows(), "failed_runs")),
      FROM(runs),
      WHERE(failed_runs(), between(runs.dt, "2026-09-01", "2026-09-24")),
      GROUP_BY(runs.dt, runs.region),
  )
  for day in by_day(fill):
      run(day, send=run_query)
  ```

  It emits `WITH ... INSERT OVERWRITE TABLE mart.daily_failures PARTITION (dt='2026-09-01') SELECT
  ...`, with the `WITH` first (the only order Hive parses, and what sqlglot gives with the Hive
  dialect).
  - **The partition written is the day of the Statement's own date bound**, the one `by_day`
    splits on. The user doesn't select the date column, and naming it in `SELECT` refuses.
  - **One day per write.** A write that covers more than one day refuses at `to_hive`/`run`, not at
    `statement(...)`, so a whole backfill can still be built and then split. The message says to
    loop over `by_day(...)`.
  - **Replace, never append.** There is no `INSERT_INTO`, so re-running a day replaces it instead of
    doubling it. The docstring notes that on Hive 2.3/3.1 under Tez a day that now comes back empty
    may keep its old rows (HIVE-18702).
  - An automatic `LIMIT`, if it is ever set, never applies to a write. A write Statement can't be
    used as a Derived table.
- **Columns line up by name, as a Guard.** Hive's `INSERT` matches columns by position, so a wrong
  order would silently fill the wrong columns. The Toolbox emits the `SELECT` in the Saved table's
  Table reference column order, leaving out the date partition column. A missing or extra column
  refuses with `GuardRefused`, naming it, with no opt-out.
- **The table is created once, from its Table reference.** `create_table(daily_failures)` returns
  `CREATE TABLE IF NOT EXISTS mart.daily_failures (region STRING, failed_runs BIGINT) PARTITIONED BY
  (dt STRING) STORED AS ORC`, which the user sends once with `run`. That is the one form every Hive
  version accepts, since a partitioned `CREATE TABLE AS` needs 4.0. It refuses, naming the columns,
  if any column in that Table reference has no type.
- **Lineage joins Statements at the top.** The lineage export takes several Statements. Where one
  writes a table that another reads, the graph continues through it. The notebook can import both,
  so no import rule breaks, and nothing is stored that can go stale.

Research facts the build needs: `to_hive` must always generate with the Hive dialect (without it,
sqlglot prints `INSERT ... WITH`, which Hive rejects). Lineage must not run sqlglot's `optimize()`
first, because it merges CTEs away. The AST key for `WITH` is `with` in sqlglot 25 and `with_`
in 30.

Handed on:

- **"What goes in a Table reference, and is it written or generated?"** A Saved table's Table
  reference must type every column, and its column order is the order the table is written in.
  Whether it is written by hand or generated from the writing Statement is decided there.
- **"What's in the Toolbox?"** It gets `derived`, `INSERT_OVERWRITE` and `create_table`, and the
  lineage export takes several Statements.
- **"What does exploring a Statement's lineage look like?"** It gets lineage joined across a Saved
  table.
- **The map's fog:** the schema-drift patch gets sharper, since `IF NOT EXISTS` leaves an existing
  table with different columns alone. The real limits at work add the Hive version, the engine and
  whether managed tables are ACID. From Hive 3.1 an ACID table refuses `INSERT OVERWRITE` combined
  with `UNION ALL`.

**Changed by "Does the Toolbox check a Table reference against the warehouse?" (2026-09-25).**
`create_table(t)` emits a plain `CREATE TABLE`, which Hive refuses when the table exists;
`create_table(t, may_exist=True)` restores `IF NOT EXISTS`.
