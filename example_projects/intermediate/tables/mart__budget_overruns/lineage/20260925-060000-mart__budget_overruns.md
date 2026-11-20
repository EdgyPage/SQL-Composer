# Lineage: write_budget_overruns_1, write_budget_overruns_2

Made by `export_lineage`. Each Statement has a section: what it reads and writes, its Run values and the Session settings sent before it, its Hive, then where each of its columns comes from.

Written as two files side by side, named alike: an HTML page, which draws the lineage, and a Markdown twin, the same sections as text, with no drawing. On the page, click a box, or press Tab until it is outlined and press Enter, to light up every box that feeds it and every box it feeds, and to open a panel on the right: for a calculated column, the column first, then the section of the Statement that makes it; for a table's column, the section of each Statement that writes or reads it. Escape, or a click on empty space, closes it.

## write_budget_overruns_1

It writes the Saved table mart.budget_overruns, replacing each partition its rows fill.

- Reads: ops.region_budgets, ops.region_costs
- Writes: mart.budget_overruns

### Hive as submitted

```sql
INSERT OVERWRITE TABLE mart.budget_overruns PARTITION(region = 'eu')
SELECT
  region_costs.job_id,
  region_budgets.budget_cents,
  COUNT(*) AS days,
  COUNT(CASE WHEN region_costs.cost_cents > region_budgets.budget_cents THEN 1 END) AS days_over
FROM ops.region_costs AS region_costs
JOIN ops.region_budgets AS region_budgets
  ON region_budgets.job_id = region_costs.job_id AND region_budgets.region = 'eu'
WHERE
  region_costs.region = 'eu' AND region_costs.dt BETWEEN '20260911' AND '20260924'
GROUP BY
  region_costs.job_id,
  region_budgets.budget_cents
```

### Calculated columns

Every column that is calculated rather than copied, in the order it is calculated.

#### `days`

Calculated in **write_budget_overruns_1** as `count_rows()`, which is `COUNT(*)`.

```text
write_budget_overruns_1.days = count_rows()
└─ (no columns: it counts rows)
```

Rows that count:

- WHERE in write_budget_overruns_1: `equals(region_costs.region, "eu")`, which is `region_costs.region = 'eu'` (reads ops.region_costs.region)
- WHERE in write_budget_overruns_1: `between(region_costs.dt, "20260911", "20260924")`, which is `region_costs.dt BETWEEN '20260911' AND '20260924'` (reads ops.region_costs.dt)
- JOIN ON in write_budget_overruns_1: `all_of(equals(region_budgets.job_id, region_costs.job_id), equals(region_budgets.region, "eu"))`, which is `region_budgets.job_id = region_costs.job_id AND region_budgets.region = 'eu'` (reads ops.region_budgets.job_id, ops.region_budgets.region, ops.region_costs.job_id)

One value for each different `region_costs.job_id` and `region_budgets.budget_cents`.

#### `days_over`

Calculated in **write_budget_overruns_1** as `count_rows(where=more_than(region_costs.cost_cents, region_budgets.budget_cents))`, which is `COUNT(CASE WHEN region_costs.cost_cents > region_budgets.budget_cents THEN 1 END)`.

```text
write_budget_overruns_1.days_over = count_rows(where=more_than(region_costs.cost_cents, region_budgets.budget_cents))
├─ ops.region_costs.cost_cents  (bigint)
└─ ops.region_budgets.budget_cents  (bigint)
```

Rows that count:

- WHERE in write_budget_overruns_1: `equals(region_costs.region, "eu")`, which is `region_costs.region = 'eu'` (reads ops.region_costs.region)
- WHERE in write_budget_overruns_1: `between(region_costs.dt, "20260911", "20260924")`, which is `region_costs.dt BETWEEN '20260911' AND '20260924'` (reads ops.region_costs.dt)
- JOIN ON in write_budget_overruns_1: `all_of(equals(region_budgets.job_id, region_costs.job_id), equals(region_budgets.region, "eu"))`, which is `region_budgets.job_id = region_costs.job_id AND region_budgets.region = 'eu'` (reads ops.region_budgets.job_id, ops.region_budgets.region, ops.region_costs.job_id)

One value for each different `region_costs.job_id` and `region_budgets.budget_cents`.

### Copied columns

- `job_id` comes from ops.region_costs.job_id
- `budget_cents` comes from ops.region_budgets.budget_cents

### Keys

The columns that tell each step's rows apart, as the Toolbox works them out. A column in one is marked "in the Key" on its box in the drawing.

- write_budget_overruns_1: Key (job_id), since GROUP_BY makes one row for each job_id.
- mart.budget_overruns' Key (job_id, region) holds: each row written has its own.

## write_budget_overruns_2

It writes the Saved table mart.budget_overruns, replacing each partition its rows fill.

- Reads: ops.region_budgets, ops.region_costs
- Writes: mart.budget_overruns

### Hive as submitted

```sql
INSERT OVERWRITE TABLE mart.budget_overruns PARTITION(region = 'us')
SELECT
  region_costs.job_id,
  region_budgets.budget_cents,
  COUNT(*) AS days,
  COUNT(CASE WHEN region_costs.cost_cents > region_budgets.budget_cents THEN 1 END) AS days_over
FROM ops.region_costs AS region_costs
JOIN ops.region_budgets AS region_budgets
  ON region_budgets.job_id = region_costs.job_id AND region_budgets.region = 'us'
WHERE
  region_costs.region = 'us' AND region_costs.dt BETWEEN '20260911' AND '20260924'
GROUP BY
  region_costs.job_id,
  region_budgets.budget_cents
```

### Calculated columns

Every column that is calculated rather than copied, in the order it is calculated.

#### `days`

Calculated in **write_budget_overruns_2** as `count_rows()`, which is `COUNT(*)`.

```text
write_budget_overruns_2.days = count_rows()
└─ (no columns: it counts rows)
```

Rows that count:

- WHERE in write_budget_overruns_2: `equals(region_costs.region, "us")`, which is `region_costs.region = 'us'` (reads ops.region_costs.region)
- WHERE in write_budget_overruns_2: `between(region_costs.dt, "20260911", "20260924")`, which is `region_costs.dt BETWEEN '20260911' AND '20260924'` (reads ops.region_costs.dt)
- JOIN ON in write_budget_overruns_2: `all_of(equals(region_budgets.job_id, region_costs.job_id), equals(region_budgets.region, "us"))`, which is `region_budgets.job_id = region_costs.job_id AND region_budgets.region = 'us'` (reads ops.region_budgets.job_id, ops.region_budgets.region, ops.region_costs.job_id)

One value for each different `region_costs.job_id` and `region_budgets.budget_cents`.

#### `days_over`

Calculated in **write_budget_overruns_2** as `count_rows(where=more_than(region_costs.cost_cents, region_budgets.budget_cents))`, which is `COUNT(CASE WHEN region_costs.cost_cents > region_budgets.budget_cents THEN 1 END)`.

```text
write_budget_overruns_2.days_over = count_rows(where=more_than(region_costs.cost_cents, region_budgets.budget_cents))
├─ ops.region_costs.cost_cents  (bigint)
└─ ops.region_budgets.budget_cents  (bigint)
```

Rows that count:

- WHERE in write_budget_overruns_2: `equals(region_costs.region, "us")`, which is `region_costs.region = 'us'` (reads ops.region_costs.region)
- WHERE in write_budget_overruns_2: `between(region_costs.dt, "20260911", "20260924")`, which is `region_costs.dt BETWEEN '20260911' AND '20260924'` (reads ops.region_costs.dt)
- JOIN ON in write_budget_overruns_2: `all_of(equals(region_budgets.job_id, region_costs.job_id), equals(region_budgets.region, "us"))`, which is `region_budgets.job_id = region_costs.job_id AND region_budgets.region = 'us'` (reads ops.region_budgets.job_id, ops.region_budgets.region, ops.region_costs.job_id)

One value for each different `region_costs.job_id` and `region_budgets.budget_cents`.

### Copied columns

- `job_id` comes from ops.region_costs.job_id
- `budget_cents` comes from ops.region_budgets.budget_cents

### Keys

The columns that tell each step's rows apart, as the Toolbox works them out. A column in one is marked "in the Key" on its box in the drawing.

- write_budget_overruns_2: Key (job_id), since GROUP_BY makes one row for each job_id.
- mart.budget_overruns' Key (job_id, region) holds: each row written has its own.

---

Made by export_lineage on 2026-09-25 06:00, from your scripts at commit nogit, with sqlglot Composer 8.9.
