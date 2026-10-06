# Lineage: write_daily_job_runs

Made by `export_lineage`. The chart is written in Mermaid, which JupyterLab draws. Arrows run from where a value comes from to where it goes. A solid arrow carries a value. A dotted arrow carries a column into a condition, or runs from a condition to the step whose rows it decides (labelled "filters"). A dotted arrow labelled "day written" runs from a write's date bound to the day of the Saved table it writes.

## Graph

```mermaid
flowchart LR
  subgraph g0["ops.job_runs"]
    n0["ops.job_runs.job_id<br/><small>bigint</small>"]
    n2["ops.job_runs.dt<br/><small>string</small>"]
    n4["ops.job_runs.status<br/><small>string</small>"]
    n6["ops.job_runs.duration_mins<br/><small>int</small>"]
  end
  subgraph g1["runs_per_job_day"]
    n1["runs_per_job_day.job_id<br/><small>job_runs.job_id</small>"]
    n3["runs_per_job_day.runs<br/><small>count_rows()</small>"]
    n5["runs_per_job_day.failed_runs<br/><small>count_rows(where=equals(job_runs.status, #quot;F…</small>"]
    n7["runs_per_job_day.minutes<br/><small>sum_of(job_runs.duration_mins)</small>"]
  end
  subgraph g2["filters on runs_per_job_day"]
    n8{{"WHERE in runs_per_job_day<br/><small>between(job_runs.dt, #quot;2026-09-24#quot;, #quot;2026-09…</small>"}}
  end
  subgraph g3["write_daily_job_runs"]
    n9["job_id<br/><small>runs_per_job_day.job_id</small>"]
    n10["runs<br/><small>runs_per_job_day.runs</small>"]
    n11["failed_runs<br/><small>runs_per_job_day.failed_runs</small>"]
    n12["minutes<br/><small>runs_per_job_day.minutes</small>"]
  end
  subgraph g4["mart.daily_job_runs"]
    n13["mart.daily_job_runs.job_id<br/><small>bigint</small>"]
    n14["mart.daily_job_runs.runs<br/><small>bigint</small>"]
    n15["mart.daily_job_runs.failed_runs<br/><small>bigint</small>"]
    n16["mart.daily_job_runs.minutes<br/><small>bigint</small>"]
    n17["mart.daily_job_runs.dt<br/><small>string</small>"]
  end
  n0 --> n1
  n4 --> n5
  n6 --> n7
  n2 -.-> n8
  n1 --> n9
  n3 --> n10
  n5 --> n11
  n7 --> n12
  n9 --> n13
  n10 --> n14
  n11 --> n15
  n12 --> n16
  n8 -.->|day written| n17
  n8 -.->|filters| g1
```

## write_daily_job_runs

It writes the Saved table mart.daily_job_runs, one day at a time.

### Calculated columns

Every column that is calculated rather than copied, in the order it is calculated.

#### `runs_per_job_day.runs`

Calculated in **runs_per_job_day** as `count_rows()`, which is `COUNT(*)`.

```text
runs_per_job_day.runs = count_rows()
└─ (no columns: it counts rows)
```

Rows that count:
- WHERE in runs_per_job_day: `between(job_runs.dt, "2026-09-24", "2026-09-24")`, which is `job_runs.dt BETWEEN '2026-09-24' AND '2026-09-24'` (reads ops.job_runs.dt)

One value for each different `job_runs.job_id` and `job_runs.dt`.

#### `runs_per_job_day.failed_runs`

Calculated in **runs_per_job_day** as `count_rows(where=equals(job_runs.status, "FAILED"))`, which is `COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END)`.

```text
runs_per_job_day.failed_runs = count_rows(where=equals(job_runs.status, "FAILED"))
└─ ops.job_runs.status  (string)
```

Rows that count:
- WHERE in runs_per_job_day: `between(job_runs.dt, "2026-09-24", "2026-09-24")`, which is `job_runs.dt BETWEEN '2026-09-24' AND '2026-09-24'` (reads ops.job_runs.dt)

One value for each different `job_runs.job_id` and `job_runs.dt`.

#### `runs_per_job_day.minutes`

Calculated in **runs_per_job_day** as `sum_of(job_runs.duration_mins)`, which is `SUM(job_runs.duration_mins)`.

```text
runs_per_job_day.minutes = sum_of(job_runs.duration_mins)
└─ ops.job_runs.duration_mins  (int)
```

Rows that count:
- WHERE in runs_per_job_day: `between(job_runs.dt, "2026-09-24", "2026-09-24")`, which is `job_runs.dt BETWEEN '2026-09-24' AND '2026-09-24'` (reads ops.job_runs.dt)

One value for each different `job_runs.job_id` and `job_runs.dt`.

### Copied columns

| Output | Comes from |
| --- | --- |
| `job_id` | runs_per_job_day.job_id ← ops.job_runs.job_id |
| `runs` | runs_per_job_day.runs (calculated) |
| `failed_runs` | runs_per_job_day.failed_runs (calculated) ← ops.job_runs.status |
| `minutes` | runs_per_job_day.minutes (calculated) ← ops.job_runs.duration_mins |

### Hive as submitted

```sql
WITH runs_per_job_day AS (
  SELECT
    job_runs.job_id,
    job_runs.dt,
    COUNT(*) AS runs,
    COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END) AS failed_runs,
    SUM(job_runs.duration_mins) AS minutes
  FROM ops.job_runs AS job_runs
  WHERE
    job_runs.dt BETWEEN '2026-09-24' AND '2026-09-24'
  GROUP BY
    job_runs.job_id,
    job_runs.dt
)
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-24')
SELECT
  runs_per_job_day.job_id,
  runs_per_job_day.runs,
  runs_per_job_day.failed_runs,
  runs_per_job_day.minutes
FROM runs_per_job_day
```

---

Made by export_lineage on 2026-09-25 06:00, from your scripts at commit pinned, with sqlglot Composer 4.1.
