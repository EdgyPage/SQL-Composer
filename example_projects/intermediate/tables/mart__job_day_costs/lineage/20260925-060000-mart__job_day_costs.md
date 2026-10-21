<!-- sqlglot Composer 6.0, exported 2026-10-21 07:24 - copy it, then edit your copy -->
# Lineage: statement_1, statement_2, statement_3

Made by `export_lineage`. The chart is written in Mermaid, which JupyterLab draws. Arrows run from where a value comes from to where it goes. A solid arrow carries a value. A dotted arrow carries a column into a condition, or runs from a condition to the step whose rows it decides (labelled "filters"). A dotted arrow labelled "day written" runs from a write's date bound to the day of the Saved table it writes.

## Graph

```mermaid
flowchart LR
  subgraph g0["ops.region_costs"]
    n0["ops.region_costs.job_id<br/><small>bigint</small><br/><small>in the Key</small>"]
    n2["ops.region_costs.dt<br/><small>string</small><br/><small>in the Key</small>"]
    n3["ops.region_costs.cost_cents<br/><small>bigint</small>"]
  end
  subgraph g1["costs_per_job_day in statement_1"]
    n1["costs_per_job_day in statement_1.job_id<br/><small>region_costs.job_id</small><br/><small>in the Key</small>"]
    n4["costs_per_job_day in statement_1.cost_cents<br/><small>sum_of(region_costs.cost_cents)</small>"]
  end
  subgraph g2["filters on costs_per_job_day in statement_1"]
    n5{{"WHERE in costs_per_job_day in statement_1<br/><small>equals(region_costs.dt, datetime.date(2026,…</small>"}}
  end
  subgraph g3["statement_1"]
    n6["job_id<br/><small>costs_per_job_day.job_id</small><br/><small>in the Key</small>"]
    n7["cost_cents<br/><small>costs_per_job_day.cost_cents</small>"]
  end
  subgraph g4["mart.job_day_costs"]
    n8["mart.job_day_costs.job_id<br/><small>bigint</small><br/><small>in the Key</small>"]
    n9["mart.job_day_costs.cost_cents<br/><small>bigint</small>"]
    n10["mart.job_day_costs.dt<br/><small>string</small><br/><small>in the Key</small>"]
  end
  subgraph g5["costs_per_job_day in statement_2"]
    n11["costs_per_job_day in statement_2.job_id<br/><small>region_costs.job_id</small><br/><small>in the Key</small>"]
    n12["costs_per_job_day in statement_2.cost_cents<br/><small>sum_of(region_costs.cost_cents)</small>"]
  end
  subgraph g6["filters on costs_per_job_day in statement_2"]
    n13{{"WHERE in costs_per_job_day in statement_2<br/><small>equals(region_costs.dt, datetime.date(2026,…</small>"}}
  end
  subgraph g7["statement_2"]
    n14["job_id<br/><small>costs_per_job_day.job_id</small><br/><small>in the Key</small>"]
    n15["cost_cents<br/><small>costs_per_job_day.cost_cents</small>"]
  end
  subgraph g8["costs_per_job_day in statement_3"]
    n16["costs_per_job_day in statement_3.job_id<br/><small>region_costs.job_id</small><br/><small>in the Key</small>"]
    n17["costs_per_job_day in statement_3.cost_cents<br/><small>sum_of(region_costs.cost_cents)</small>"]
  end
  subgraph g9["filters on costs_per_job_day in statement_3"]
    n18{{"WHERE in costs_per_job_day in statement_3<br/><small>equals(region_costs.dt, datetime.date(2026,…</small>"}}
  end
  subgraph g10["statement_3"]
    n19["job_id<br/><small>costs_per_job_day.job_id</small><br/><small>in the Key</small>"]
    n20["cost_cents<br/><small>costs_per_job_day.cost_cents</small>"]
  end
  n0 --> n1
  n3 --> n4
  n2 -.-> n5
  n1 --> n6
  n4 --> n7
  n6 --> n8
  n7 --> n9
  n5 -.->|day written| n10
  n0 --> n11
  n3 --> n12
  n2 -.-> n13
  n11 --> n14
  n12 --> n15
  n14 --> n8
  n15 --> n9
  n13 -.->|day written| n10
  n0 --> n16
  n3 --> n17
  n2 -.-> n18
  n16 --> n19
  n17 --> n20
  n19 --> n8
  n20 --> n9
  n18 -.->|day written| n10
  n5 -.->|filters| g1
  n13 -.->|filters| g5
  n18 -.->|filters| g8
```

## statement_1

It writes the Saved table mart.job_day_costs, one day at a time.

### Calculated columns

Every column that is calculated rather than copied, in the order it is calculated.

#### `costs_per_job_day in statement_1.cost_cents`

Calculated in **costs_per_job_day in statement_1** as `sum_of(region_costs.cost_cents)`, which is `SUM(region_costs.cost_cents)`.

```text
costs_per_job_day in statement_1.cost_cents = sum_of(region_costs.cost_cents)
└─ ops.region_costs.cost_cents  (bigint)
```

Rows that count:
- WHERE in costs_per_job_day in statement_1: `equals(region_costs.dt, datetime.date(2026, 9, 22))`, which is `region_costs.dt = '20260922'` (reads ops.region_costs.dt)

One value for each different `region_costs.job_id` and `region_costs.dt`.

### Copied columns

| Output | Comes from |
| --- | --- |
| `job_id` | costs_per_job_day in statement_1.job_id ← ops.region_costs.job_id |
| `cost_cents` | costs_per_job_day in statement_1.cost_cents (calculated) ← ops.region_costs.cost_cents |

### Keys

The columns that tell each step's rows apart, as the Toolbox works them out. A column in one is marked "in the Key" in the chart.

- derived('costs_per_job_day', ...): Key (job_id), since GROUP_BY makes one row for each job_id, dt, with dt held to one value.
- statement_1: Key (job_id), since costs_per_job_day's rows are told apart by job_id.
- mart.job_day_costs' Key (job_id, dt) holds: each row written has its own.

### Hive as submitted

```sql
WITH costs_per_job_day AS (
  SELECT
    region_costs.job_id,
    region_costs.dt,
    SUM(region_costs.cost_cents) AS cost_cents
  FROM ops.region_costs AS region_costs
  WHERE
    region_costs.dt = '20260922'
  GROUP BY
    region_costs.job_id,
    region_costs.dt
)
INSERT OVERWRITE TABLE mart.job_day_costs PARTITION(dt = '2026-09-22')
SELECT
  costs_per_job_day.job_id,
  costs_per_job_day.cost_cents
FROM costs_per_job_day
```

## statement_2

It writes the Saved table mart.job_day_costs, one day at a time.

### Calculated columns

Every column that is calculated rather than copied, in the order it is calculated.

#### `costs_per_job_day in statement_2.cost_cents`

Calculated in **costs_per_job_day in statement_2** as `sum_of(region_costs.cost_cents)`, which is `SUM(region_costs.cost_cents)`.

```text
costs_per_job_day in statement_2.cost_cents = sum_of(region_costs.cost_cents)
└─ ops.region_costs.cost_cents  (bigint)
```

Rows that count:
- WHERE in costs_per_job_day in statement_2: `equals(region_costs.dt, datetime.date(2026, 9, 23))`, which is `region_costs.dt = '20260923'` (reads ops.region_costs.dt)

One value for each different `region_costs.job_id` and `region_costs.dt`.

### Copied columns

| Output | Comes from |
| --- | --- |
| `job_id` | costs_per_job_day in statement_2.job_id ← ops.region_costs.job_id |
| `cost_cents` | costs_per_job_day in statement_2.cost_cents (calculated) ← ops.region_costs.cost_cents |

### Keys

The columns that tell each step's rows apart, as the Toolbox works them out. A column in one is marked "in the Key" in the chart.

- derived('costs_per_job_day', ...): Key (job_id), since GROUP_BY makes one row for each job_id, dt, with dt held to one value.
- statement_2: Key (job_id), since costs_per_job_day's rows are told apart by job_id.
- mart.job_day_costs' Key (job_id, dt) holds: each row written has its own.

### Hive as submitted

```sql
WITH costs_per_job_day AS (
  SELECT
    region_costs.job_id,
    region_costs.dt,
    SUM(region_costs.cost_cents) AS cost_cents
  FROM ops.region_costs AS region_costs
  WHERE
    region_costs.dt = '20260923'
  GROUP BY
    region_costs.job_id,
    region_costs.dt
)
INSERT OVERWRITE TABLE mart.job_day_costs PARTITION(dt = '2026-09-23')
SELECT
  costs_per_job_day.job_id,
  costs_per_job_day.cost_cents
FROM costs_per_job_day
```

## statement_3

It writes the Saved table mart.job_day_costs, one day at a time.

### Calculated columns

Every column that is calculated rather than copied, in the order it is calculated.

#### `costs_per_job_day in statement_3.cost_cents`

Calculated in **costs_per_job_day in statement_3** as `sum_of(region_costs.cost_cents)`, which is `SUM(region_costs.cost_cents)`.

```text
costs_per_job_day in statement_3.cost_cents = sum_of(region_costs.cost_cents)
└─ ops.region_costs.cost_cents  (bigint)
```

Rows that count:
- WHERE in costs_per_job_day in statement_3: `equals(region_costs.dt, datetime.date(2026, 9, 24))`, which is `region_costs.dt = '20260924'` (reads ops.region_costs.dt)

One value for each different `region_costs.job_id` and `region_costs.dt`.

### Copied columns

| Output | Comes from |
| --- | --- |
| `job_id` | costs_per_job_day in statement_3.job_id ← ops.region_costs.job_id |
| `cost_cents` | costs_per_job_day in statement_3.cost_cents (calculated) ← ops.region_costs.cost_cents |

### Keys

The columns that tell each step's rows apart, as the Toolbox works them out. A column in one is marked "in the Key" in the chart.

- derived('costs_per_job_day', ...): Key (job_id), since GROUP_BY makes one row for each job_id, dt, with dt held to one value.
- statement_3: Key (job_id), since costs_per_job_day's rows are told apart by job_id.
- mart.job_day_costs' Key (job_id, dt) holds: each row written has its own.

### Hive as submitted

```sql
WITH costs_per_job_day AS (
  SELECT
    region_costs.job_id,
    region_costs.dt,
    SUM(region_costs.cost_cents) AS cost_cents
  FROM ops.region_costs AS region_costs
  WHERE
    region_costs.dt = '20260924'
  GROUP BY
    region_costs.job_id,
    region_costs.dt
)
INSERT OVERWRITE TABLE mart.job_day_costs PARTITION(dt = '2026-09-24')
SELECT
  costs_per_job_day.job_id,
  costs_per_job_day.cost_cents
FROM costs_per_job_day
```

---

Made by export_lineage on 2026-09-25 06:00, from your scripts at commit nogit, with sqlglot Composer 6.0.
