# Lineage: written

Made by `export_lineage`. The chart is written in Mermaid, which JupyterLab draws. Arrows run from where a value comes from to where it goes. A solid arrow carries a value. A dotted arrow carries a column into a condition, or runs from a condition to the step whose rows it decides (labelled "filters"). A dotted arrow labelled "day written" runs from a write's date bound to the day of the Saved table it writes.

## Graph

```mermaid
flowchart LR
  subgraph g0["written"]
    n0["row_count<br/><small>count_rows()</small>"]
  end
  subgraph g1["filters on written"]
    n1{{"WHERE in written<br/><small>between(job_events.dt, #quot;2026-09-24#quot;, #quot;2026-…</small>"}}
  end
  subgraph g2["ops.job_events"]
    n2["ops.job_events.dt<br/><small>string</small>"]
  end
  subgraph g3["mart.job_events_checks"]
    n3["mart.job_events_checks.row_count<br/><small>bigint</small>"]
    n4["mart.job_events_checks.dt<br/><small>string</small><br/><small>in the Key</small>"]
  end
  n2 -.-> n1
  n0 --> n3
  n1 -.->|day written| n4
  n1 -.->|filters| g0
```

## written

It writes the Saved table mart.job_events_checks, one day at a time.

### Calculated columns

Every column that is calculated rather than copied, in the order it is calculated.

#### `row_count`

Calculated in **written** as `count_rows()`, which is `COUNT(*)`.

```text
written.row_count = count_rows()
└─ (no columns: it counts rows)
```

Rows that count:
- WHERE in written: `between(job_events.dt, "2026-09-24", "2026-09-24")`, which is `job_events.dt BETWEEN '2026-09-24' AND '2026-09-24'` (reads ops.job_events.dt)

One value for each different `job_events.dt`.

### Keys

The columns that tell each step's rows apart, as the Toolbox works them out. A column in one is marked "in the Key" in the chart.

- written: one row, so it needs no Key: GROUP_BY makes one row for each dt, with dt held to one value.
- mart.job_events_checks' Key (dt) holds: each row written has its own.

### Hive as submitted

```sql
INSERT OVERWRITE TABLE mart.job_events_checks PARTITION(dt = '2026-09-24')
SELECT
  COUNT(*) AS row_count
FROM ops.job_events AS job_events
WHERE
  job_events.dt BETWEEN '2026-09-24' AND '2026-09-24'
GROUP BY
  job_events.dt
```

---

Made by export_lineage on 2026-09-25 06:00, from your scripts at commit pinned, with sqlglot Composer 6.0.
