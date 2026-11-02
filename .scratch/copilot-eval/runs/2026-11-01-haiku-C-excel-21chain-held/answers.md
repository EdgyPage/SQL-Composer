date: 2026-11-01
arm: C
model: haiku
files: 21chain-held

## X78

### Map

Each piece's role:
- Excel Table Parameters: settings, empty, read by no formula. Not a source, step or final.
- Excel Table Keys: settings, empty. No value is typed over a formula, so no Keys row is needed. Not a source, step or final.
- Excel Table region_costs: source (typed columns only, and no query loads it).
- Power Query known_costs: step (cost_per_job's M names it).
- Excel Table known_costs: final (loaded by Power Query known_costs; no other Table's formula reads it).
- Excel Table known_costs (Total Row): final of its own.
- Power Query cost_per_job: step (the query that loads Table cost_per_job).
- Excel Table cost_per_job: step (job_dollars' SUMIFS reads it).
- Excel Table job_dollars: final, and a summary (its only typed column, job_id, is what its SUMIFS match on).

Sources:
- region_costs (job_id, cost_cents, region, dt), read as `<database>.region_costs`.

Steps:
- known_costs (Power Query): a CTE `known_costs` that reads region_costs, keeps the rows whose cost_cents is not blank, and selects job_id, cost_cents, dt. region is dropped.
- cost_per_job (Power Query, feeding Table cost_per_job): a CTE `cost_per_job` that reads known_costs, GROUP BY job_id, with total_cents = SUM(cost_cents). Its sums (1770, 1690, 1160) match the Table's typed rows.

Finals:
- known_costs (job_id, cost_cents, dt, dollars): rows from the query known_costs; dollars is cost_cents / 100.
- known_costs (Total Row) (cost_cents): one column, SUM(cost_cents) AS cost_cents. The "Total" label and the empty cells get no column.
- job_dollars (job_id, dollars): summary. Its typed job_id values 1, 2 and 3 are typed in as its groups. dollars is its SUMIFS over cost_per_job: a LEFT JOIN, COALESCE(.., 0), then / 100.

Values typed over a formula: none. Every formula cell in known_costs and job_dollars holds the one formula down its column.

Marks: none.

Refusals: none.

Left alone: the Steps sheet and the notes in D1 of Parameters and Keys (cells outside a Table); Parameters and Keys themselves, which are empty settings; no charts or PivotTables.

Note: region_costs row 29 has a blank cost_cents (job 2, dt 20260924). The known_costs query's `<> null` becomes `IS NOT NULL`, so that row is dropped, as M drops it. No formula reads that blank, so no COALESCE is needed.

To fill in: `<database>`, in each read of region_costs (three places: the known_costs final, the known_costs Total Row, and job_dollars).

### Hive

```sql
WITH known_costs AS (
  SELECT job_id, cost_cents, dt
  FROM <database>.region_costs
  WHERE cost_cents IS NOT NULL
)
SELECT job_id, cost_cents, dt, cost_cents / 100 AS dollars
FROM known_costs
```

```sql
WITH known_costs AS (
  WITH known_costs AS (
    SELECT job_id, cost_cents, dt
    FROM <database>.region_costs
    WHERE cost_cents IS NOT NULL
  )
  SELECT job_id, cost_cents, dt, cost_cents / 100 AS dollars
  FROM known_costs
)
SELECT SUM(cost_cents) AS cost_cents
FROM known_costs
```

```sql
WITH known_costs AS (
  SELECT job_id, cost_cents, dt
  FROM <database>.region_costs
  WHERE cost_cents IS NOT NULL
),
cost_per_job AS (
  SELECT job_id, SUM(cost_cents) AS total_cents
  FROM known_costs
  GROUP BY job_id
)
SELECT j.job_id, COALESCE(c.total, 0) / 100 AS dollars
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (SELECT job_id, SUM(total_cents) AS total FROM cost_per_job GROUP BY job_id) c
  ON j.job_id = c.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
