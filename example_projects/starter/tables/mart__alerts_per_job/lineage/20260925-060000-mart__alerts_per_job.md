# Lineage: written

Made by `export_lineage`. The chart is written in Mermaid, which JupyterLab draws. Arrows run from where a value comes from to where it goes. A solid arrow carries a value. A dotted arrow carries a column into a condition, or runs from a condition to the step whose rows it decides (labelled "filters"). A dotted arrow labelled "day written" runs from a write's date bound to the day of the Saved table it writes.

## Graph

```mermaid
flowchart LR
  subgraph g0["ops.job_runs"]
    n0["ops.job_runs.job_id<br/><small>bigint</small>"]
    n8["ops.job_runs.dt<br/><small>string</small>"]
    n10["ops.job_runs.run_id<br/><small>bigint</small><br/><small>in the Key</small>"]
  end
  subgraph g1["written"]
    n1["job_id<br/><small>job_runs.job_id</small><br/><small>in the Key</small>"]
    n2["alerts<br/><small>count_rows()</small>"]
    n4["high_alerts<br/><small>count_rows(where=equals(run_alerts.severity…</small>"]
  end
  subgraph g2["ops.run_alerts"]
    n3["ops.run_alerts.severity<br/><small>string</small>"]
    n6["ops.run_alerts.dt<br/><small>string</small>"]
    n11["ops.run_alerts.run_id<br/><small>bigint</small>"]
  end
  subgraph g3["filters on written"]
    n5{{"WHERE in written<br/><small>between(run_alerts.dt, #quot;2026-09-24#quot;, #quot;2026-…</small>"}}
    n7{{"WHERE in written<br/><small>between(job_runs.dt, #quot;2026-09-23#quot;, #quot;2026-09…</small>"}}
    n9{{"JOIN ON in written<br/><small>equals(job_runs.run_id, run_alerts.run_id)</small>"}}
  end
  subgraph g4["mart.alerts_per_job"]
    n12["mart.alerts_per_job.job_id<br/><small>bigint</small><br/><small>in the Key</small>"]
    n13["mart.alerts_per_job.alerts<br/><small>bigint</small>"]
    n14["mart.alerts_per_job.high_alerts<br/><small>bigint</small>"]
    n15["mart.alerts_per_job.dt<br/><small>string</small><br/><small>in the Key</small>"]
  end
  n0 --> n1
  n3 --> n4
  n6 -.-> n5
  n8 -.-> n7
  n10 -.-> n9
  n11 -.-> n9
  n1 --> n12
  n2 --> n13
  n4 --> n14
  n5 -.->|day written| n15
  n5 -.->|filters| g1
  n7 -.->|filters| g1
  n9 -.->|filters| g1
```

## written

It writes the Saved table mart.alerts_per_job, one day at a time.

### Calculated columns

Every column that is calculated rather than copied, in the order it is calculated.

#### `alerts`

Calculated in **written** as `count_rows()`, which is `COUNT(*)`.

```text
written.alerts = count_rows()
└─ (no columns: it counts rows)
```

Rows that count:
- WHERE in written: `between(run_alerts.dt, "2026-09-24", "2026-09-24")`, which is `run_alerts.dt BETWEEN '2026-09-24' AND '2026-09-24'` (reads ops.run_alerts.dt)
- WHERE in written: `between(job_runs.dt, "2026-09-23", "2026-09-24")`, which is `job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'` (reads ops.job_runs.dt)
- JOIN ON in written: `equals(job_runs.run_id, run_alerts.run_id)`, which is `job_runs.run_id = run_alerts.run_id` (reads ops.job_runs.run_id, ops.run_alerts.run_id)

One value for each different `run_alerts.dt` and `job_runs.job_id`.

#### `high_alerts`

Calculated in **written** as `count_rows(where=equals(run_alerts.severity, "high"))`, which is `COUNT(CASE WHEN run_alerts.severity = 'high' THEN 1 END)`.

```text
written.high_alerts = count_rows(where=equals(run_alerts.severity, "high"))
└─ ops.run_alerts.severity  (string)
```

Rows that count:
- WHERE in written: `between(run_alerts.dt, "2026-09-24", "2026-09-24")`, which is `run_alerts.dt BETWEEN '2026-09-24' AND '2026-09-24'` (reads ops.run_alerts.dt)
- WHERE in written: `between(job_runs.dt, "2026-09-23", "2026-09-24")`, which is `job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'` (reads ops.job_runs.dt)
- JOIN ON in written: `equals(job_runs.run_id, run_alerts.run_id)`, which is `job_runs.run_id = run_alerts.run_id` (reads ops.job_runs.run_id, ops.run_alerts.run_id)

One value for each different `run_alerts.dt` and `job_runs.job_id`.

### Copied columns

| Output | Comes from |
| --- | --- |
| `job_id` | ops.job_runs.job_id |

### Keys

The columns that tell each step's rows apart, as the Toolbox works them out. A column in one is marked "in the Key" in the chart.

- written: Key (job_id), since GROUP_BY makes one row for each job_id, dt, with dt held to one value.
- mart.alerts_per_job's Key (job_id, dt) holds: each row written has its own.

### Hive as submitted

```sql
INSERT OVERWRITE TABLE mart.alerts_per_job PARTITION(dt = '2026-09-24')
SELECT
  job_runs.job_id,
  COUNT(*) AS alerts,
  COUNT(CASE WHEN run_alerts.severity = 'high' THEN 1 END) AS high_alerts
FROM ops.run_alerts AS run_alerts
JOIN ops.job_runs AS job_runs
  ON job_runs.run_id = run_alerts.run_id
WHERE
  run_alerts.dt BETWEEN '2026-09-24' AND '2026-09-24'
  AND job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
GROUP BY
  run_alerts.dt,
  job_runs.job_id
```

---

Made by export_lineage on 2026-09-25 06:00, from your scripts at commit pinned, with sqlglot Composer 6.0.
