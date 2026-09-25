# Which Hive query shapes choke a cluster, and what does strict mode already refuse?

Type: research
Status: resolved
Blocked by: -
Findings: branch `research/hive-load-hazards`, file `research/hive-load-hazards.md`

## Question

Load safety is a default in this effort, and it needs a concrete list rather than a feeling. From
primary Hive documentation, establish:

- Exactly what `hive.mapred.mode=strict` and its successors (`hive.strict.checks.*`) refuse -
  a missing partition filter, `ORDER BY` without `LIMIT`, Cartesian products, anything else - and
  in which Hive versions each check exists.
- The other query shapes that commonly exhaust CPU or memory, especially for a beginner: unbounded
  `SELECT *`, a global `ORDER BY` funnelled through one reducer, `COUNT(DISTINCT ...)` over huge
  sets, skewed joins, `LATERAL VIEW explode` blow-ups.
- Idiomatic ways to bound work and results in Hive: iterating over partition ranges, what `LIMIT`
  does without `ORDER BY`, `TABLESAMPLE`, and why `OFFSET`-style paging is expensive.

The findings feed the two guardrail tickets.

## Answer

Hive's own strict mode cannot be relied on, so the Toolbox has to enforce its own defaults.

Strict mode is a set of separate `hive.strict.checks.*` switches, each refusing at compile time
with a `SemanticException`:

- `ORDER BY` without `LIMIT`, and a missing partition filter: one `large.query` switch in 2.x,
  split in two in 3.0, off by default in both;
- Cartesian products: on in 2.x, off from 3.0;
- unsafe type comparisons: on;
- `LOAD` into bucketed tables: on;
- `OFFSET` without `ORDER BY`: 4.0 and later, off.

Setting the deprecated `hive.mapred.mode` to any value overrides all of them. Even switched on,
the partition check only asks whether a filter *mentions* a partition column, not how many
partitions it reads. Worse, a plain `SELECT *` skips Hive's size threshold and is streamed whole
through HiveServer2 - which is precisely the "select star chokes the notebook" case the user named.

The defaults the Toolbox should enforce, each with a named opt-out:

1. a **bounded** partition filter, not merely a present one;
2. an automatic `LIMIT` on anything returned to the notebook;
3. no `ORDER BY` without a `LIMIT`;
4. no cross joins;
5. no `OFFSET` paging - chunk by partition or key range instead;
6. explicit column lists instead of `*`.

Not verified: the error text as a client sees it (read from source, not a live server; the work
API may wrap it). Several places where Hive's docs disagree with its source (`hive.mapred.mode`'s
2.x default, `hive.limit.pushdown.memory.usage`, `hive.map.aggr`, a deprecation version) were
resolved in favour of the source. `LIMIT` short-circuiting the scan was checked on the Tez path
only. The work cluster's Hive version, its strict settings and whether its API accepts `SET` were
added to "What does the work environment actually have?".

Findings: branch `research/hive-load-hazards` (commit `b23e779`), file
`research/hive-load-hazards.md`.
