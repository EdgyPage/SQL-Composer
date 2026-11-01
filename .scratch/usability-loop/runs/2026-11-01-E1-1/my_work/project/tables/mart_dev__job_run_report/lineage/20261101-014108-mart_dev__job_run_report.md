# Lineage: statement

Made by `export_lineage`. The chart is written in Mermaid, which JupyterLab draws. Arrows run from where a value comes from to where it goes. A solid arrow carries a value. A dotted arrow carries a column into a condition, or runs from a condition to the step whose rows it decides (labelled "filters").

## Graph

```mermaid
flowchart LR
  subgraph g0["ops.job_runs"]
    n0["ops.job_runs.job_id<br/><small>bigint</small>"]
    n3["ops.job_runs.status<br/><small>string</small>"]
    n5["ops.job_runs.duration_mins<br/><small>int</small>"]
  end
  subgraph g1["statement"]
    n1["job_id<br/><small>job_runs.job_id</small><br/><small>in the Key</small>"]
    n2["runs<br/><small>fill_null(count_rows(), 0)</small>"]
    n4["failed_runs<br/><small>fill_null(count_rows(where=equals(job_runs.…</small>"]
    n6["avg_duration_mins<br/><small>average_of(job_runs.duration_mins)</small>"]
  end
  subgraph g2["mart_dev.job_run_report"]
    n7["mart_dev.job_run_report.job_id<br/><small>bigint</small><br/><small>in the Key</small>"]
    n8["mart_dev.job_run_report.runs<br/><small>bigint</small>"]
    n9["mart_dev.job_run_report.failed_runs<br/><small>bigint</small>"]
    n10["mart_dev.job_run_report.avg_duration_mins<br/><small>double</small>"]
  end
  n0 --> n1
  n3 --> n4
  n5 --> n6
  n1 --> n7
  n2 --> n8
  n4 --> n9
  n6 --> n10
```

## statement

It writes the whole Saved table mart_dev.job_run_report.

### Calculated columns

Every column that is calculated rather than copied, in the order it is calculated.

#### `runs`

Calculated in **statement** as `fill_null(count_rows(), 0)`, which is `COALESCE(COUNT(*), 0)`.

```text
statement.runs = fill_null(count_rows(), 0)
└─ (no columns: it counts rows)
```

One value for each different `job_runs.job_id`.

#### `failed_runs`

Calculated in **statement** as `fill_null(count_rows(where=equals(job_runs.status, "FAILED")), 0)`, which is `COALESCE(COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END), 0)`.

```text
statement.failed_runs = fill_null(count_rows(where=equals(job_runs.status, "FAILED")), 0)
└─ ops.job_runs.status  (string)
```

One value for each different `job_runs.job_id`.

#### `avg_duration_mins`

Calculated in **statement** as `average_of(job_runs.duration_mins)`, which is `AVG(job_runs.duration_mins)`.

```text
statement.avg_duration_mins = average_of(job_runs.duration_mins)
└─ ops.job_runs.duration_mins  (int)
```

One value for each different `job_runs.job_id`.

### Copied columns

| Output | Comes from |
| --- | --- |
| `job_id` | ops.job_runs.job_id |

### Keys

The columns that tell each step's rows apart, as the Toolbox works them out. A column in one is marked "in the Key" in the chart.

- statement: Key (job_id), since GROUP_BY makes one row for each job_id.
- mart_dev.job_run_report's Key (job_id) holds: each row written has its own.

### Hive as submitted

```sql
INSERT OVERWRITE TABLE mart_dev.job_run_report
SELECT
  job_runs.job_id,
  COALESCE(COUNT(*), 0) AS runs,
  COALESCE(COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END), 0) AS failed_runs,
  AVG(job_runs.duration_mins) AS avg_duration_mins
FROM ops.job_runs AS job_runs
GROUP BY
  job_runs.job_id
```

---

Made by export_lineage on 2026-11-01 01:41, from your scripts at commit nogit, with sqlglot Composer 8.1, exported 2026-11-01 01:25.
