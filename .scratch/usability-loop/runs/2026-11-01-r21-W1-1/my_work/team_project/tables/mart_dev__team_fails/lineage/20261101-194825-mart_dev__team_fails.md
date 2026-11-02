# Lineage: statement

Made by `export_lineage`. The chart is written in Mermaid, which JupyterLab draws. Arrows run from where a value comes from to where it goes. A solid arrow carries a value. A dotted arrow carries a column into a condition, or runs from a condition to the step whose rows it decides (labelled "filters").

## Graph

```mermaid
flowchart LR
  subgraph g0["ops.job_runs"]
    n0["ops.job_runs.job_id<br/><small>bigint</small>"]
    n2["ops.job_runs.dt<br/><small>string</small>"]
    n5["ops.job_runs.status<br/><small>string</small>"]
  end
  subgraph g1["f"]
    n1["f.job_id<br/><small>r.job_id</small>"]
    n3["f.dt<br/><small>r.dt</small>"]
  end
  subgraph g2["filters on f"]
    n4{{"WHERE in f<br/><small>equals(r.status, #quot;FAILED#quot;)</small>"}}
  end
  subgraph g3["ops.job_owners"]
    n6["ops.job_owners.team<br/><small>string</small>"]
    n11["ops.job_owners.job_id<br/><small>bigint</small>"]
  end
  subgraph g4["statement"]
    n7["team<br/><small>o.team</small><br/><small>in the Key</small>"]
    n8["fails<br/><small>count_rows()</small>"]
    n9["dt<br/><small>f.dt</small><br/><small>in the Key</small>"]
  end
  subgraph g5["filters on statement"]
    n10{{"JOIN ON in statement<br/><small>equals(f.job_id, o.job_id)</small>"}}
  end
  subgraph g6["mart_dev.team_fails"]
    n12["mart_dev.team_fails.team<br/><small>string</small><br/><small>in the Key</small>"]
    n13["mart_dev.team_fails.fails<br/><small>bigint</small>"]
    n14["mart_dev.team_fails.dt<br/><small>string</small><br/><small>in the Key</small>"]
  end
  n0 --> n1
  n2 --> n3
  n5 -.-> n4
  n6 --> n7
  n3 --> n9
  n1 -.-> n10
  n11 -.-> n10
  n7 --> n12
  n8 --> n13
  n9 --> n14
  n4 -.->|filters| g1
  n10 -.->|filters| g4
```

## statement

It writes the Saved table mart_dev.team_fails, replacing each partition its rows fill.

### Calculated columns

Every column that is calculated rather than copied, in the order it is calculated.

#### `fails`

Calculated in **statement** as `count_rows()`, which is `COUNT(*)`.

```text
statement.fails = count_rows()
└─ (no columns: it counts rows)
```

Rows that count:
- WHERE in f: `equals(r.status, "FAILED")`, which is `r.status = 'FAILED'` (reads ops.job_runs.status)
- JOIN ON in statement: `equals(f.job_id, o.job_id)`, which is `f.job_id = o.job_id` (reads ops.job_owners.job_id, ops.job_runs.job_id)

One value for each different `o.team` and `f.dt`.

### Copied columns

| Output | Comes from |
| --- | --- |
| `team` | ops.job_owners.team |
| `dt` | f.dt ← ops.job_runs.dt |

### Keys

The columns that tell each step's rows apart, as the Toolbox works them out. A column in one is marked "in the Key" in the chart.

- derived('f', ...): no Key the Toolbox can see, since r declares no Key.
- statement: Key (team, dt), since GROUP_BY makes one row for each team, dt.
- mart_dev.team_fails' Key (team, dt) holds: each row written has its own.

### Hive as submitted

```sql
WITH f AS (
  SELECT
    r.job_id,
    r.dt
  FROM ops.job_runs AS r
  WHERE
    r.status = 'FAILED'
)
INSERT OVERWRITE TABLE mart_dev.team_fails PARTITION(dt)
SELECT
  o.team,
  COUNT(*) AS fails,
  f.dt
FROM f
JOIN ops.job_owners AS o
  ON f.job_id = o.job_id
GROUP BY
  o.team,
  f.dt
```

---

Made by export_lineage on 2026-11-01 19:48, from your scripts at commit nogit, with sqlglot Composer 8.2, exported 2026-11-01 19:41.
