# Which Hive query shapes choke a cluster, and what does strict mode already refuse?

Type: research
Status: open
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
