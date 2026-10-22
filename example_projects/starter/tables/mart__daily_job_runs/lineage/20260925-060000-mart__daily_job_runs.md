# Lineage: write_daily_job_runs

Made by `export_lineage`. The chart is written in Mermaid, which JupyterLab draws. Arrows run from where a value comes from to where it goes. A solid arrow carries a value. A dotted arrow carries a column into a condition, or runs from a condition to the step whose rows it decides (labelled "filters").

## Graph

```mermaid
flowchart LR
  subgraph g0["ops.job_runs"]
    n0["ops.job_runs.job_id<br/><small>bigint</small>"]
    n2["ops.job_runs.dt<br/><small>string</small>"]
    n5["ops.job_runs.status<br/><small>string</small>"]
    n7["ops.job_runs.duration_mins<br/><small>int</small>"]
  end
  subgraph g1["runs_per_job"]
    n1["runs_per_job.job_id<br/><small>job_runs.job_id</small><br/><small>in the Key</small>"]
    n3["runs_per_job.dt<br/><small>job_runs.dt</small>"]
    n4["runs_per_job.runs<br/><small>count_rows()</small>"]
    n6["runs_per_job.failed_runs<br/><small>count_rows(where=equals(job_runs.status, #quot;F…</small>"]
    n8["runs_per_job.minutes<br/><small>sum_of(job_runs.duration_mins)</small>"]
  end
  subgraph g2["filters on runs_per_job"]
    n9{{"WHERE in runs_per_job<br/><small>equals(job_runs.dt, #quot;2026-09-24#quot;)</small>"}}
  end
  subgraph g3["write_daily_job_runs"]
    n10["job_id<br/><small>runs_per_job.job_id</small><br/><small>in the Key</small>"]
    n11["runs<br/><small>runs_per_job.runs</small>"]
    n12["failed_runs<br/><small>runs_per_job.failed_runs</small>"]
    n13["minutes<br/><small>runs_per_job.minutes</small>"]
    n14["dt<br/><small>runs_per_job.dt</small>"]
  end
  subgraph g4["mart.daily_job_runs"]
    n15["mart.daily_job_runs.job_id<br/><small>bigint</small><br/><small>in the Key</small>"]
    n16["mart.daily_job_runs.runs<br/><small>bigint</small>"]
    n17["mart.daily_job_runs.failed_runs<br/><small>bigint</small>"]
    n18["mart.daily_job_runs.minutes<br/><small>bigint</small>"]
    n19["mart.daily_job_runs.dt<br/><small>string</small><br/><small>in the Key</small>"]
  end
  n0 --> n1
  n2 --> n3
  n5 --> n6
  n7 --> n8
  n2 -.-> n9
  n1 --> n10
  n4 --> n11
  n6 --> n12
  n8 --> n13
  n3 --> n14
  n10 --> n15
  n11 --> n16
  n12 --> n17
  n13 --> n18
  n14 --> n19
  n9 -.->|filters| g1
```

## write_daily_job_runs

It writes the Saved table mart.daily_job_runs, replacing each partition its rows fill.

### Calculated columns

Every column that is calculated rather than copied, in the order it is calculated.

#### `runs_per_job.runs`

Calculated in **runs_per_job** as `count_rows()`, which is `COUNT(*)`.

```text
runs_per_job.runs = count_rows()
└─ (no columns: it counts rows)
```

Rows that count:
- WHERE in runs_per_job: `equals(job_runs.dt, "2026-09-24")`, which is `job_runs.dt = '2026-09-24'` (reads ops.job_runs.dt)

One value for each different `job_runs.job_id` and `job_runs.dt`.

#### `runs_per_job.failed_runs`

Calculated in **runs_per_job** as `count_rows(where=equals(job_runs.status, "FAILED"))`, which is `COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END)`.

```text
runs_per_job.failed_runs = count_rows(where=equals(job_runs.status, "FAILED"))
└─ ops.job_runs.status  (string)
```

Rows that count:
- WHERE in runs_per_job: `equals(job_runs.dt, "2026-09-24")`, which is `job_runs.dt = '2026-09-24'` (reads ops.job_runs.dt)

One value for each different `job_runs.job_id` and `job_runs.dt`.

#### `runs_per_job.minutes`

Calculated in **runs_per_job** as `sum_of(job_runs.duration_mins)`, which is `SUM(job_runs.duration_mins)`.

```text
runs_per_job.minutes = sum_of(job_runs.duration_mins)
└─ ops.job_runs.duration_mins  (int)
```

Rows that count:
- WHERE in runs_per_job: `equals(job_runs.dt, "2026-09-24")`, which is `job_runs.dt = '2026-09-24'` (reads ops.job_runs.dt)

One value for each different `job_runs.job_id` and `job_runs.dt`.

### Copied columns

| Output | Comes from |
| --- | --- |
| `job_id` | runs_per_job.job_id ← ops.job_runs.job_id |
| `runs` | runs_per_job.runs (calculated) |
| `failed_runs` | runs_per_job.failed_runs (calculated) ← ops.job_runs.status |
| `minutes` | runs_per_job.minutes (calculated) ← ops.job_runs.duration_mins |
| `dt` | runs_per_job.dt ← ops.job_runs.dt |

### Keys

The columns that tell each step's rows apart, as the Toolbox works them out. A column in one is marked "in the Key" in the chart.

- derived('runs_per_job', ...): Key (job_id), since GROUP_BY makes one row for each job_id, dt, with dt held to one value.
- write_daily_job_runs: Key (job_id), since runs_per_job's rows are told apart by job_id.
- mart.daily_job_runs' Key (job_id, dt) holds: each row written has its own.

### Hive as submitted

```sql
WITH runs_per_job AS (
  SELECT
    job_runs.job_id,
    job_runs.dt,
    COUNT(*) AS runs,
    COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END) AS failed_runs,
    SUM(job_runs.duration_mins) AS minutes
  FROM ops.job_runs AS job_runs
  WHERE
    job_runs.dt = '2026-09-24'
  GROUP BY
    job_runs.job_id,
    job_runs.dt
)
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt)
SELECT
  runs_per_job.job_id,
  runs_per_job.runs,
  runs_per_job.failed_runs,
  runs_per_job.minutes,
  runs_per_job.dt
FROM runs_per_job
```

---

Made by export_lineage on 2026-09-25 06:00, from your scripts at commit nogit, with sqlglot Composer 7.0.
