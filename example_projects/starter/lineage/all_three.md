# Lineage: write_daily_job_runs, write_alerts_per_job, write_team_day

Made by `export_lineage`. The chart is written in Mermaid, which JupyterLab draws. Arrows run from where a value comes from to where it goes. A solid arrow carries a value. A dotted arrow carries a column into a condition, or runs from a condition to the step whose rows it decides (labelled "filters"). A dotted arrow labelled "day written" runs from a write's date bound to the day of the Saved table it writes.

## Graph

```mermaid
flowchart LR
  subgraph g0["ops.job_runs"]
    n0["ops.job_runs.job_id<br/><small>bigint</small>"]
    n2["ops.job_runs.dt<br/><small>string</small>"]
    n4["ops.job_runs.status<br/><small>string</small>"]
    n6["ops.job_runs.duration_mins<br/><small>int</small>"]
    n26["ops.job_runs.run_id<br/><small>bigint</small>"]
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
  subgraph g5["write_alerts_per_job"]
    n18["job_id<br/><small>job_runs.job_id</small>"]
    n19["alerts<br/><small>count_rows()</small>"]
    n21["high_alerts<br/><small>count_rows(where=equals(run_alerts.severity…</small>"]
  end
  subgraph g6["ops.run_alerts"]
    n20["ops.run_alerts.severity<br/><small>string</small>"]
    n23["ops.run_alerts.dt<br/><small>string</small>"]
    n27["ops.run_alerts.run_id<br/><small>bigint</small>"]
  end
  subgraph g7["filters on write_alerts_per_job"]
    n22{{"WHERE in write_alerts_per_job<br/><small>equals(run_alerts.dt, #quot;2026-09-24#quot;)</small>"}}
    n24{{"WHERE in write_alerts_per_job<br/><small>between(job_runs.dt, #quot;2026-09-23#quot;, #quot;2026-09…</small>"}}
    n25{{"JOIN ON in write_alerts_per_job<br/><small>equals(job_runs.run_id, run_alerts.run_id)</small>"}}
  end
  subgraph g8["mart.alerts_per_job"]
    n28["mart.alerts_per_job.job_id<br/><small>bigint</small>"]
    n29["mart.alerts_per_job.alerts<br/><small>bigint</small>"]
    n30["mart.alerts_per_job.high_alerts<br/><small>bigint</small>"]
    n31["mart.alerts_per_job.dt<br/><small>string</small>"]
  end
  subgraph g9["ops.jobs"]
    n32["ops.jobs.team<br/><small>string</small>"]
    n41["ops.jobs.job_id<br/><small>bigint</small>"]
  end
  subgraph g10["write_team_day"]
    n33["team<br/><small>jobs.team</small>"]
    n34["runs<br/><small>sum_of(daily_job_runs.runs)</small>"]
    n35["failed_runs<br/><small>sum_of(daily_job_runs.failed_runs)</small>"]
    n36["minutes<br/><small>sum_of(daily_job_runs.minutes)</small>"]
    n37["alerts<br/><small>fill_null(sum_of(alerts_per_job.alerts), 0)</small>"]
    n38["high_alerts<br/><small>fill_null(sum_of(alerts_per_job.high_alerts…</small>"]
  end
  subgraph g11["filters on write_team_day"]
    n39{{"WHERE in write_team_day<br/><small>equals(daily_job_runs.dt, #quot;2026-09-24#quot;)</small>"}}
    n40{{"JOIN ON in write_team_day<br/><small>equals(jobs.job_id, daily_job_runs.job_id)</small>"}}
    n42{{"LEFT JOIN ON in write_team_day<br/><small>all_of(equals(alerts_per_job.job_id, daily_…</small>"}}
  end
  subgraph g12["mart.team_day"]
    n43["mart.team_day.team<br/><small>string</small>"]
    n44["mart.team_day.runs<br/><small>bigint</small>"]
    n45["mart.team_day.failed_runs<br/><small>bigint</small>"]
    n46["mart.team_day.minutes<br/><small>bigint</small>"]
    n47["mart.team_day.alerts<br/><small>bigint</small>"]
    n48["mart.team_day.high_alerts<br/><small>bigint</small>"]
    n49["mart.team_day.dt<br/><small>string</small>"]
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
  n0 --> n18
  n20 --> n21
  n23 -.-> n22
  n2 -.-> n24
  n26 -.-> n25
  n27 -.-> n25
  n18 --> n28
  n19 --> n29
  n21 --> n30
  n22 -.->|day written| n31
  n32 --> n33
  n14 --> n34
  n15 --> n35
  n16 --> n36
  n29 --> n37
  n30 --> n38
  n17 -.-> n39
  n41 -.-> n40
  n13 -.-> n40
  n28 -.-> n42
  n13 -.-> n42
  n31 -.-> n42
  n33 --> n43
  n34 --> n44
  n35 --> n45
  n36 --> n46
  n37 --> n47
  n38 --> n48
  n39 -.->|day written| n49
  n8 -.->|filters| g1
  n22 -.->|filters| g5
  n24 -.->|filters| g5
  n25 -.->|filters| g5
  n39 -.->|filters| g10
  n40 -.->|filters| g10
  n42 -.->|filters| g10
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

## write_alerts_per_job

It writes the Saved table mart.alerts_per_job, one day at a time.

### Calculated columns

Every column that is calculated rather than copied, in the order it is calculated.

#### `alerts`

Calculated in **write_alerts_per_job** as `count_rows()`, which is `COUNT(*)`.

```text
write_alerts_per_job.alerts = count_rows()
└─ (no columns: it counts rows)
```

Rows that count:
- WHERE in write_alerts_per_job: `equals(run_alerts.dt, "2026-09-24")`, which is `run_alerts.dt = '2026-09-24'` (reads ops.run_alerts.dt)
- WHERE in write_alerts_per_job: `between(job_runs.dt, "2026-09-23", "2026-09-24")`, which is `job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'` (reads ops.job_runs.dt)
- JOIN ON in write_alerts_per_job: `equals(job_runs.run_id, run_alerts.run_id)`, which is `job_runs.run_id = run_alerts.run_id` (reads ops.job_runs.run_id, ops.run_alerts.run_id)

One value for each different `job_runs.job_id`.

#### `high_alerts`

Calculated in **write_alerts_per_job** as `count_rows(where=equals(run_alerts.severity, "high"))`, which is `COUNT(CASE WHEN run_alerts.severity = 'high' THEN 1 END)`.

```text
write_alerts_per_job.high_alerts = count_rows(where=equals(run_alerts.severity, "high"))
└─ ops.run_alerts.severity  (string)
```

Rows that count:
- WHERE in write_alerts_per_job: `equals(run_alerts.dt, "2026-09-24")`, which is `run_alerts.dt = '2026-09-24'` (reads ops.run_alerts.dt)
- WHERE in write_alerts_per_job: `between(job_runs.dt, "2026-09-23", "2026-09-24")`, which is `job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'` (reads ops.job_runs.dt)
- JOIN ON in write_alerts_per_job: `equals(job_runs.run_id, run_alerts.run_id)`, which is `job_runs.run_id = run_alerts.run_id` (reads ops.job_runs.run_id, ops.run_alerts.run_id)

One value for each different `job_runs.job_id`.

### Copied columns

| Output | Comes from |
| --- | --- |
| `job_id` | ops.job_runs.job_id |

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
  run_alerts.dt = '2026-09-24'
  AND job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
GROUP BY
  job_runs.job_id
```

## write_team_day

It reads the Saved table mart.alerts_per_job, written by write_alerts_per_job above. It reads the Saved table mart.daily_job_runs, written by write_daily_job_runs above. It writes the Saved table mart.team_day, one day at a time.

### Calculated columns

Every column that is calculated rather than copied, in the order it is calculated.

#### `runs`

Calculated in **write_team_day** as `sum_of(daily_job_runs.runs)`, which is `SUM(daily_job_runs.runs)`.

```text
write_team_day.runs = sum_of(daily_job_runs.runs)
└─ mart.daily_job_runs.runs  (bigint)
   └─ write_daily_job_runs.runs
      └─ runs_per_job_day.runs = count_rows()
```

Rows that count:
- WHERE in write_team_day: `equals(daily_job_runs.dt, "2026-09-24")`, which is `daily_job_runs.dt = '2026-09-24'` (reads mart.daily_job_runs.dt)
- JOIN ON in write_team_day: `equals(jobs.job_id, daily_job_runs.job_id)`, which is `jobs.job_id = daily_job_runs.job_id` (reads mart.daily_job_runs.job_id, ops.jobs.job_id)
- LEFT JOIN ON in write_team_day: `all_of(equals(alerts_per_job.job_id, daily_job_runs.job_id), equals(alerts_per_job.dt, "2026-09-24"))`, which is `alerts_per_job.job_id = daily_job_runs.job_id AND alerts_per_job.dt = '2026-09-24'` (reads mart.alerts_per_job.dt, mart.alerts_per_job.job_id, mart.daily_job_runs.job_id)

One value for each different `jobs.team`.

#### `failed_runs`

Calculated in **write_team_day** as `sum_of(daily_job_runs.failed_runs)`, which is `SUM(daily_job_runs.failed_runs)`.

```text
write_team_day.failed_runs = sum_of(daily_job_runs.failed_runs)
└─ mart.daily_job_runs.failed_runs  (bigint)
   └─ write_daily_job_runs.failed_runs
      └─ runs_per_job_day.failed_runs = count_rows(where=equals(job_runs.status, "FAILED"))
         └─ ops.job_runs.status  (string)
```

Rows that count:
- WHERE in write_team_day: `equals(daily_job_runs.dt, "2026-09-24")`, which is `daily_job_runs.dt = '2026-09-24'` (reads mart.daily_job_runs.dt)
- JOIN ON in write_team_day: `equals(jobs.job_id, daily_job_runs.job_id)`, which is `jobs.job_id = daily_job_runs.job_id` (reads mart.daily_job_runs.job_id, ops.jobs.job_id)
- LEFT JOIN ON in write_team_day: `all_of(equals(alerts_per_job.job_id, daily_job_runs.job_id), equals(alerts_per_job.dt, "2026-09-24"))`, which is `alerts_per_job.job_id = daily_job_runs.job_id AND alerts_per_job.dt = '2026-09-24'` (reads mart.alerts_per_job.dt, mart.alerts_per_job.job_id, mart.daily_job_runs.job_id)

One value for each different `jobs.team`.

#### `minutes`

Calculated in **write_team_day** as `sum_of(daily_job_runs.minutes)`, which is `SUM(daily_job_runs.minutes)`.

```text
write_team_day.minutes = sum_of(daily_job_runs.minutes)
└─ mart.daily_job_runs.minutes  (bigint)
   └─ write_daily_job_runs.minutes
      └─ runs_per_job_day.minutes = sum_of(job_runs.duration_mins)
         └─ ops.job_runs.duration_mins  (int)
```

Rows that count:
- WHERE in write_team_day: `equals(daily_job_runs.dt, "2026-09-24")`, which is `daily_job_runs.dt = '2026-09-24'` (reads mart.daily_job_runs.dt)
- JOIN ON in write_team_day: `equals(jobs.job_id, daily_job_runs.job_id)`, which is `jobs.job_id = daily_job_runs.job_id` (reads mart.daily_job_runs.job_id, ops.jobs.job_id)
- LEFT JOIN ON in write_team_day: `all_of(equals(alerts_per_job.job_id, daily_job_runs.job_id), equals(alerts_per_job.dt, "2026-09-24"))`, which is `alerts_per_job.job_id = daily_job_runs.job_id AND alerts_per_job.dt = '2026-09-24'` (reads mart.alerts_per_job.dt, mart.alerts_per_job.job_id, mart.daily_job_runs.job_id)

One value for each different `jobs.team`.

#### `alerts`

Calculated in **write_team_day** as `fill_null(sum_of(alerts_per_job.alerts), 0)`, which is `COALESCE(SUM(alerts_per_job.alerts), 0)`.

```text
write_team_day.alerts = fill_null(sum_of(alerts_per_job.alerts), 0)
└─ mart.alerts_per_job.alerts  (bigint)
   └─ write_alerts_per_job.alerts = count_rows()
```

Rows that count:
- WHERE in write_alerts_per_job: `between(job_runs.dt, "2026-09-23", "2026-09-24")`, which is `job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'` (reads ops.job_runs.dt)
- JOIN ON in write_alerts_per_job: `equals(job_runs.run_id, run_alerts.run_id)`, which is `job_runs.run_id = run_alerts.run_id` (reads ops.job_runs.run_id, ops.run_alerts.run_id)
- WHERE in write_team_day: `equals(daily_job_runs.dt, "2026-09-24")`, which is `daily_job_runs.dt = '2026-09-24'` (reads mart.daily_job_runs.dt)
- JOIN ON in write_team_day: `equals(jobs.job_id, daily_job_runs.job_id)`, which is `jobs.job_id = daily_job_runs.job_id` (reads mart.daily_job_runs.job_id, ops.jobs.job_id)
- LEFT JOIN ON in write_team_day: `all_of(equals(alerts_per_job.job_id, daily_job_runs.job_id), equals(alerts_per_job.dt, "2026-09-24"))`, which is `alerts_per_job.job_id = daily_job_runs.job_id AND alerts_per_job.dt = '2026-09-24'` (reads mart.alerts_per_job.dt, mart.alerts_per_job.job_id, mart.daily_job_runs.job_id)

One value for each different `jobs.team`.

#### `high_alerts`

Calculated in **write_team_day** as `fill_null(sum_of(alerts_per_job.high_alerts), 0)`, which is `COALESCE(SUM(alerts_per_job.high_alerts), 0)`.

```text
write_team_day.high_alerts = fill_null(sum_of(alerts_per_job.high_alerts), 0)
└─ mart.alerts_per_job.high_alerts  (bigint)
   └─ write_alerts_per_job.high_alerts = count_rows(where=equals(run_alerts.severity, "high"))
      └─ ops.run_alerts.severity  (string)
```

Rows that count:
- WHERE in write_alerts_per_job: `between(job_runs.dt, "2026-09-23", "2026-09-24")`, which is `job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'` (reads ops.job_runs.dt)
- JOIN ON in write_alerts_per_job: `equals(job_runs.run_id, run_alerts.run_id)`, which is `job_runs.run_id = run_alerts.run_id` (reads ops.job_runs.run_id, ops.run_alerts.run_id)
- WHERE in write_team_day: `equals(daily_job_runs.dt, "2026-09-24")`, which is `daily_job_runs.dt = '2026-09-24'` (reads mart.daily_job_runs.dt)
- JOIN ON in write_team_day: `equals(jobs.job_id, daily_job_runs.job_id)`, which is `jobs.job_id = daily_job_runs.job_id` (reads mart.daily_job_runs.job_id, ops.jobs.job_id)
- LEFT JOIN ON in write_team_day: `all_of(equals(alerts_per_job.job_id, daily_job_runs.job_id), equals(alerts_per_job.dt, "2026-09-24"))`, which is `alerts_per_job.job_id = daily_job_runs.job_id AND alerts_per_job.dt = '2026-09-24'` (reads mart.alerts_per_job.dt, mart.alerts_per_job.job_id, mart.daily_job_runs.job_id)

One value for each different `jobs.team`.

### Copied columns

| Output | Comes from |
| --- | --- |
| `team` | ops.jobs.team |

### Hive as submitted

```sql
INSERT OVERWRITE TABLE mart.team_day PARTITION(dt = '2026-09-24')
SELECT
  jobs.team,
  SUM(daily_job_runs.runs) AS runs,
  SUM(daily_job_runs.failed_runs) AS failed_runs,
  SUM(daily_job_runs.minutes) AS minutes,
  COALESCE(SUM(alerts_per_job.alerts), 0) AS alerts,
  COALESCE(SUM(alerts_per_job.high_alerts), 0) AS high_alerts
FROM mart.daily_job_runs AS daily_job_runs
JOIN ops.jobs AS jobs
  ON jobs.job_id = daily_job_runs.job_id
LEFT JOIN mart.alerts_per_job AS alerts_per_job
  ON alerts_per_job.job_id = daily_job_runs.job_id
  AND alerts_per_job.dt = '2026-09-24'
WHERE
  daily_job_runs.dt = '2026-09-24'
GROUP BY
  jobs.team
```

---

Made by export_lineage on 2026-09-25 06:00, from your scripts at commit pinned, with sqlglot Composer 3.2.
