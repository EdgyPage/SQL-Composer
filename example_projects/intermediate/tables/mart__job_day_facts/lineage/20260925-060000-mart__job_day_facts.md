<!-- sqlglot Composer 7.2 - copy it, then edit your copy -->
# Lineage: write_job_day_facts

Made by `export_lineage`. The chart is written in Mermaid, which JupyterLab draws. Arrows run from where a value comes from to where it goes. A solid arrow carries a value. A dotted arrow carries a column into a condition, or runs from a condition to the step whose rows it decides (labelled "filters").

## Graph

```mermaid
flowchart LR
  subgraph g0["ops.job_events"]
    n0["ops.job_events.job_id<br/><small>bigint</small>"]
    n2["ops.job_events.dt<br/><small>string</small>"]
    n5["ops.job_events.event_type<br/><small>string</small>"]
    n7["ops.job_events.minutes<br/><small>int</small>"]
  end
  subgraph g1["events_per_job"]
    n1["events_per_job.job_id<br/><small>job_events.job_id</small><br/><small>in the Key</small>"]
    n3["events_per_job.dt<br/><small>job_events.dt</small><br/><small>in the Key</small>"]
    n4["events_per_job.events<br/><small>count_rows()</small>"]
    n6["events_per_job.runs<br/><small>count_rows(where=equals(job_events.event_ty…</small>"]
    n8["events_per_job.minutes<br/><small>fill_null(sum_of(job_events.minutes, where=…</small>"]
  end
  subgraph g2["filters on events_per_job"]
    n9{{"WHERE in events_per_job<br/><small>between(job_events.dt, #quot;2026-09-22#quot;, #quot;2026-…</small>"}}
  end
  subgraph g3["write_job_day_facts"]
    n10["job_id<br/><small>events_per_job.job_id</small><br/><small>in the Key</small>"]
    n12["team<br/><small>job_owners.team</small>"]
    n13["events<br/><small>events_per_job.events</small>"]
    n14["runs<br/><small>events_per_job.runs</small>"]
    n15["minutes<br/><small>events_per_job.minutes</small>"]
    n16["dt<br/><small>events_per_job.dt</small><br/><small>in the Key</small>"]
  end
  subgraph g4["ops.job_owners"]
    n11["ops.job_owners.team<br/><small>string</small>"]
    n18["ops.job_owners.dt<br/><small>string</small><br/><small>in the Key</small>"]
    n19["ops.job_owners.job_id<br/><small>bigint</small><br/><small>in the Key</small>"]
  end
  subgraph g5["filters on write_job_day_facts"]
    n17{{"LEFT JOIN ON in write_job_day_facts<br/><small>all_of(equals(job_owners.job_id, events_per…</small>"}}
  end
  subgraph g6["mart.job_day_facts"]
    n20["mart.job_day_facts.job_id<br/><small>bigint</small><br/><small>in the Key</small>"]
    n21["mart.job_day_facts.team<br/><small>string</small>"]
    n22["mart.job_day_facts.events<br/><small>bigint</small>"]
    n23["mart.job_day_facts.runs<br/><small>bigint</small>"]
    n24["mart.job_day_facts.minutes<br/><small>bigint</small>"]
    n25["mart.job_day_facts.dt<br/><small>string</small><br/><small>in the Key</small>"]
  end
  n0 --> n1
  n2 --> n3
  n5 --> n6
  n7 --> n8
  n5 --> n8
  n2 -.-> n9
  n1 --> n10
  n11 --> n12
  n4 --> n13
  n6 --> n14
  n8 --> n15
  n3 --> n16
  n18 -.-> n17
  n19 -.-> n17
  n1 -.-> n17
  n3 -.-> n17
  n10 --> n20
  n12 --> n21
  n13 --> n22
  n14 --> n23
  n15 --> n24
  n16 --> n25
  n9 -.->|filters| g1
  n17 -.->|filters| g3
```

## write_job_day_facts

It writes the Saved table mart.job_day_facts, replacing each partition its rows fill.

### Calculated columns

Every column that is calculated rather than copied, in the order it is calculated.

#### `events_per_job.events`

Calculated in **events_per_job** as `count_rows()`, which is `COUNT(*)`.

```text
events_per_job.events = count_rows()
└─ (no columns: it counts rows)
```

Rows that count:
- WHERE in events_per_job: `between(job_events.dt, "2026-09-22", "2026-09-24")`, which is `job_events.dt BETWEEN '2026-09-22' AND '2026-09-24'` (reads ops.job_events.dt)

One value for each different `job_events.job_id` and `job_events.dt`.

#### `events_per_job.runs`

Calculated in **events_per_job** as `count_rows(where=equals(job_events.event_type, "start"))`, which is `COUNT(CASE WHEN job_events.event_type = 'start' THEN 1 END)`.

```text
events_per_job.runs = count_rows(where=equals(job_events.event_type, "start"))
└─ ops.job_events.event_type  (string)
```

Rows that count:
- WHERE in events_per_job: `between(job_events.dt, "2026-09-22", "2026-09-24")`, which is `job_events.dt BETWEEN '2026-09-22' AND '2026-09-24'` (reads ops.job_events.dt)

One value for each different `job_events.job_id` and `job_events.dt`.

#### `events_per_job.minutes`

Calculated in **events_per_job** as `fill_null(sum_of(job_events.minutes, where=is_in(job_events.event_type, ["finish", "fail"])), 0)`, which is `COALESCE(SUM(CASE WHEN job_events.event_type IN ('finish', 'fail') THEN job_events.minutes END), 0)`.

```text
events_per_job.minutes = fill_null(sum_of(job_events.minutes, where=is_in(job_events.event_type, ["finish", "fail"])), 0)
├─ ops.job_events.minutes  (int)
└─ ops.job_events.event_type  (string)
```

Rows that count:
- WHERE in events_per_job: `between(job_events.dt, "2026-09-22", "2026-09-24")`, which is `job_events.dt BETWEEN '2026-09-22' AND '2026-09-24'` (reads ops.job_events.dt)

One value for each different `job_events.job_id` and `job_events.dt`.

### Copied columns

| Output | Comes from |
| --- | --- |
| `job_id` | events_per_job.job_id ← ops.job_events.job_id |
| `team` | ops.job_owners.team |
| `events` | events_per_job.events (calculated) |
| `runs` | events_per_job.runs (calculated) ← ops.job_events.event_type |
| `minutes` | events_per_job.minutes (calculated) ← ops.job_events.minutes |
| `dt` | events_per_job.dt ← ops.job_events.dt |

### Keys

The columns that tell each step's rows apart, as the Toolbox works them out. A column in one is marked "in the Key" in the chart.

- derived('events_per_job', ...): Key (job_id, dt), since GROUP_BY makes one row for each job_id, dt.
- write_job_day_facts: Key (job_id, dt), since events_per_job's rows are told apart by job_id, dt.
- mart.job_day_facts' Key (job_id, dt) holds: each row written has its own.

### Hive as submitted

```sql
WITH events_per_job AS (
  SELECT
    job_events.job_id,
    job_events.dt,
    COUNT(*) AS events,
    COUNT(CASE WHEN job_events.event_type = 'start' THEN 1 END) AS runs,
    COALESCE(
      SUM(
        CASE WHEN job_events.event_type IN ('finish', 'fail') THEN job_events.minutes END
      ),
      0
    ) AS minutes
  FROM ops.job_events AS job_events
  WHERE
    job_events.dt BETWEEN '2026-09-22' AND '2026-09-24'
  GROUP BY
    job_events.job_id,
    job_events.dt
)
INSERT OVERWRITE TABLE mart.job_day_facts PARTITION(dt)
SELECT
  events_per_job.job_id,
  job_owners.team,
  events_per_job.events,
  events_per_job.runs,
  events_per_job.minutes,
  events_per_job.dt
FROM events_per_job
LEFT JOIN ops.job_owners AS job_owners
  ON job_owners.job_id = events_per_job.job_id
  AND job_owners.dt = events_per_job.dt
  AND job_owners.dt BETWEEN '2026-09-22' AND '2026-09-24'
```

---

Made by export_lineage on 2026-09-25 06:00, from your scripts at commit nogit, with sqlglot Composer 7.2.
