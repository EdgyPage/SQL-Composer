# Lineage: write_job_day_facts, write_team_days

Made by `export_lineage`. The chart is written in Mermaid, which JupyterLab draws. Arrows run from where a value comes from to where it goes. A solid arrow carries a value. A dotted arrow carries a column into a condition, or runs from a condition to the step whose rows it decides (labelled "filters"). A dotted arrow labelled "day written" runs from a write's date bound to the day of the Saved table it writes.

## Graph

```mermaid
flowchart LR
  subgraph g0["ops.job_events"]
    n0["ops.job_events.job_id<br/><small>bigint</small>"]
    n2["ops.job_events.dt<br/><small>string</small>"]
    n5["ops.job_events.event_type<br/><small>string</small>"]
    n7["ops.job_events.minutes<br/><small>int</small>"]
  end
  subgraph g1["events_per_job_day"]
    n1["events_per_job_day.job_id<br/><small>job_events.job_id</small>"]
    n3["events_per_job_day.dt<br/><small>job_events.dt</small>"]
    n4["events_per_job_day.events<br/><small>count_rows()</small>"]
    n6["events_per_job_day.runs<br/><small>count_rows(where=equals(job_events.event_ty…</small>"]
    n8["events_per_job_day.minutes<br/><small>fill_null(sum_of(job_events.minutes, where=…</small>"]
  end
  subgraph g2["filters on events_per_job_day"]
    n9{{"WHERE in events_per_job_day<br/><small>equals(job_events.dt, datetime.date(2026, 9…</small>"}}
  end
  subgraph g3["write_job_day_facts"]
    n10["job_id<br/><small>events_per_job_day.job_id</small>"]
    n12["team<br/><small>job_owners.team</small>"]
    n13["events<br/><small>events_per_job_day.events</small>"]
    n14["runs<br/><small>events_per_job_day.runs</small>"]
    n15["minutes<br/><small>events_per_job_day.minutes</small>"]
  end
  subgraph g4["ops.job_owners"]
    n11["ops.job_owners.team<br/><small>string</small>"]
    n17["ops.job_owners.dt<br/><small>string</small>"]
    n18["ops.job_owners.job_id<br/><small>bigint</small>"]
  end
  subgraph g5["filters on write_job_day_facts"]
    n16{{"LEFT JOIN ON in write_job_day_facts<br/><small>all_of(equals(job_owners.job_id, events_per…</small>"}}
  end
  subgraph g6["mart.job_day_facts"]
    n19["mart.job_day_facts.job_id<br/><small>bigint</small>"]
    n20["mart.job_day_facts.team<br/><small>string</small>"]
    n21["mart.job_day_facts.events<br/><small>bigint</small>"]
    n22["mart.job_day_facts.runs<br/><small>bigint</small>"]
    n23["mart.job_day_facts.minutes<br/><small>bigint</small>"]
    n24["mart.job_day_facts.dt<br/><small>string</small>"]
  end
  subgraph g7["write_team_days"]
    n25["team<br/><small>job_day_facts.team</small>"]
    n26["events<br/><small>sum_of(job_day_facts.events)</small>"]
    n27["runs<br/><small>sum_of(job_day_facts.runs)</small>"]
    n28["minutes<br/><small>sum_of(job_day_facts.minutes)</small>"]
    n30["cost_cents<br/><small>sum_of(job_day_costs.cost_cents)</small>"]
  end
  subgraph g8["mart.job_day_costs"]
    n29["mart.job_day_costs.cost_cents<br/><small>bigint</small>"]
    n33["mart.job_day_costs.dt<br/><small>string</small>"]
    n34["mart.job_day_costs.job_id<br/><small>bigint</small>"]
  end
  subgraph g9["filters on write_team_days"]
    n31{{"WHERE in write_team_days<br/><small>equals(job_day_facts.dt, datetime.date(2026…</small>"}}
    n32{{"LEFT JOIN ON in write_team_days<br/><small>all_of(equals(job_day_costs.job_id, job_day…</small>"}}
  end
  subgraph g10["mart.team_days"]
    n35["mart.team_days.team<br/><small>string</small>"]
    n36["mart.team_days.events<br/><small>bigint</small>"]
    n37["mart.team_days.runs<br/><small>bigint</small>"]
    n38["mart.team_days.minutes<br/><small>bigint</small>"]
    n39["mart.team_days.cost_cents<br/><small>bigint</small>"]
    n40["mart.team_days.dt<br/><small>string</small>"]
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
  n17 -.-> n16
  n18 -.-> n16
  n1 -.-> n16
  n3 -.-> n16
  n10 --> n19
  n12 --> n20
  n13 --> n21
  n14 --> n22
  n15 --> n23
  n9 -.->|day written| n24
  n20 --> n25
  n21 --> n26
  n22 --> n27
  n23 --> n28
  n29 --> n30
  n24 -.-> n31
  n33 -.-> n32
  n34 -.-> n32
  n19 -.-> n32
  n24 -.-> n32
  n25 --> n35
  n26 --> n36
  n27 --> n37
  n28 --> n38
  n30 --> n39
  n31 -.->|day written| n40
  n9 -.->|filters| g1
  n16 -.->|filters| g3
  n31 -.->|filters| g7
  n32 -.->|filters| g7
```

## write_job_day_facts

It writes the Saved table mart.job_day_facts, one day at a time.

### Calculated columns

Every column that is calculated rather than copied, in the order it is calculated.

#### `events_per_job_day.events`

Calculated in **events_per_job_day** as `count_rows()`, which is `COUNT(*)`.

```text
events_per_job_day.events = count_rows()
└─ (no columns: it counts rows)
```

Rows that count:
- WHERE in events_per_job_day: `equals(job_events.dt, datetime.date(2026, 9, 24))`, which is `job_events.dt = '2026-09-24'` (reads ops.job_events.dt)

One value for each different `job_events.job_id` and `job_events.dt`.

#### `events_per_job_day.runs`

Calculated in **events_per_job_day** as `count_rows(where=equals(job_events.event_type, "start"))`, which is `COUNT(CASE WHEN job_events.event_type = 'start' THEN 1 END)`.

```text
events_per_job_day.runs = count_rows(where=equals(job_events.event_type, "start"))
└─ ops.job_events.event_type  (string)
```

Rows that count:
- WHERE in events_per_job_day: `equals(job_events.dt, datetime.date(2026, 9, 24))`, which is `job_events.dt = '2026-09-24'` (reads ops.job_events.dt)

One value for each different `job_events.job_id` and `job_events.dt`.

#### `events_per_job_day.minutes`

Calculated in **events_per_job_day** as `fill_null(sum_of(job_events.minutes, where=equals(job_events.event_type, "finish")), 0)`, which is `COALESCE(SUM(CASE WHEN job_events.event_type = 'finish' THEN job_events.minutes END), 0)`.

```text
events_per_job_day.minutes = fill_null(sum_of(job_events.minutes, where=equals(job_events.event_type, "finish")), 0)
├─ ops.job_events.minutes  (int)
└─ ops.job_events.event_type  (string)
```

Rows that count:
- WHERE in events_per_job_day: `equals(job_events.dt, datetime.date(2026, 9, 24))`, which is `job_events.dt = '2026-09-24'` (reads ops.job_events.dt)

One value for each different `job_events.job_id` and `job_events.dt`.

### Copied columns

| Output | Comes from |
| --- | --- |
| `job_id` | events_per_job_day.job_id ← ops.job_events.job_id |
| `team` | ops.job_owners.team |
| `events` | events_per_job_day.events (calculated) |
| `runs` | events_per_job_day.runs (calculated) ← ops.job_events.event_type |
| `minutes` | events_per_job_day.minutes (calculated) ← ops.job_events.minutes |

### Hive as submitted

```sql
WITH events_per_job_day AS (
  SELECT
    job_events.job_id,
    job_events.dt,
    COUNT(*) AS events,
    COUNT(CASE WHEN job_events.event_type = 'start' THEN 1 END) AS runs,
    COALESCE(SUM(CASE WHEN job_events.event_type = 'finish' THEN job_events.minutes END), 0) AS minutes
  FROM ops.job_events AS job_events
  WHERE
    job_events.dt = '2026-09-24'
  GROUP BY
    job_events.job_id,
    job_events.dt
)
INSERT OVERWRITE TABLE mart.job_day_facts PARTITION(dt = '2026-09-24')
SELECT
  events_per_job_day.job_id,
  job_owners.team,
  events_per_job_day.events,
  events_per_job_day.runs,
  events_per_job_day.minutes
FROM events_per_job_day
LEFT JOIN ops.job_owners AS job_owners
  ON job_owners.job_id = events_per_job_day.job_id
  AND job_owners.dt = events_per_job_day.dt
  AND job_owners.dt BETWEEN '2026-09-24' AND '2026-09-24'
```

## write_team_days

It reads the Saved table mart.job_day_facts, written by write_job_day_facts above. It writes the Saved table mart.team_days, one day at a time.

### Calculated columns

Every column that is calculated rather than copied, in the order it is calculated.

#### `events`

Calculated in **write_team_days** as `sum_of(job_day_facts.events)`, which is `SUM(job_day_facts.events)`.

```text
write_team_days.events = sum_of(job_day_facts.events)
└─ mart.job_day_facts.events  (bigint)
   └─ write_job_day_facts.events
      └─ events_per_job_day.events = count_rows()
```

Rows that count:
- WHERE in write_team_days: `equals(job_day_facts.dt, datetime.date(2026, 9, 24))`, which is `job_day_facts.dt = '2026-09-24'` (reads mart.job_day_facts.dt)

One value for each different `job_day_facts.dt` and `job_day_facts.team`.

#### `runs`

Calculated in **write_team_days** as `sum_of(job_day_facts.runs)`, which is `SUM(job_day_facts.runs)`.

```text
write_team_days.runs = sum_of(job_day_facts.runs)
└─ mart.job_day_facts.runs  (bigint)
   └─ write_job_day_facts.runs
      └─ events_per_job_day.runs = count_rows(where=equals(job_events.event_type, "start"))
         └─ ops.job_events.event_type  (string)
```

Rows that count:
- WHERE in write_team_days: `equals(job_day_facts.dt, datetime.date(2026, 9, 24))`, which is `job_day_facts.dt = '2026-09-24'` (reads mart.job_day_facts.dt)

One value for each different `job_day_facts.dt` and `job_day_facts.team`.

#### `minutes`

Calculated in **write_team_days** as `sum_of(job_day_facts.minutes)`, which is `SUM(job_day_facts.minutes)`.

```text
write_team_days.minutes = sum_of(job_day_facts.minutes)
└─ mart.job_day_facts.minutes  (bigint)
   └─ write_job_day_facts.minutes
      └─ events_per_job_day.minutes = fill_null(sum_of(job_events.minutes, where=equals(job_events.event_type, "finish")), 0)
         ├─ ops.job_events.minutes  (int)
         └─ ops.job_events.event_type  (string)
```

Rows that count:
- WHERE in write_team_days: `equals(job_day_facts.dt, datetime.date(2026, 9, 24))`, which is `job_day_facts.dt = '2026-09-24'` (reads mart.job_day_facts.dt)

One value for each different `job_day_facts.dt` and `job_day_facts.team`.

#### `cost_cents`

Calculated in **write_team_days** as `sum_of(job_day_costs.cost_cents)`, which is `SUM(job_day_costs.cost_cents)`.

```text
write_team_days.cost_cents = sum_of(job_day_costs.cost_cents)
└─ mart.job_day_costs.cost_cents  (bigint)
```

Rows that count:
- WHERE in write_team_days: `equals(job_day_facts.dt, datetime.date(2026, 9, 24))`, which is `job_day_facts.dt = '2026-09-24'` (reads mart.job_day_facts.dt)
- LEFT JOIN ON in write_team_days: `all_of(equals(job_day_costs.job_id, job_day_facts.job_id), equals(job_day_costs.dt, job_day_facts.dt), between(job_day_costs.dt, "2026-09-24", "2026-09-24"))`, which is `job_day_costs.job_id = job_day_facts.job_id AND job_day_costs.dt = job_day_facts.dt AND job_day_costs.dt BETWEEN '2026-09-24' AND '2026-09-24'` (reads mart.job_day_costs.dt, mart.job_day_costs.job_id, mart.job_day_facts.dt, mart.job_day_facts.job_id)

One value for each different `job_day_facts.dt` and `job_day_facts.team`.

### Copied columns

| Output | Comes from |
| --- | --- |
| `team` | mart.job_day_facts.team ← write_job_day_facts.team ← ops.job_owners.team |

### Hive as submitted

```sql
INSERT OVERWRITE TABLE mart.team_days PARTITION(dt = '2026-09-24')
SELECT
  job_day_facts.team,
  SUM(job_day_facts.events) AS events,
  SUM(job_day_facts.runs) AS runs,
  SUM(job_day_facts.minutes) AS minutes,
  SUM(job_day_costs.cost_cents) AS cost_cents
FROM mart.job_day_facts AS job_day_facts
LEFT JOIN mart.job_day_costs AS job_day_costs
  ON job_day_costs.job_id = job_day_facts.job_id
  AND job_day_costs.dt = job_day_facts.dt
  AND job_day_costs.dt BETWEEN '2026-09-24' AND '2026-09-24'
WHERE
  job_day_facts.dt = '2026-09-24'
GROUP BY
  job_day_facts.dt,
  job_day_facts.team
```

---

Made by export_lineage on 2026-09-25 06:00, from your scripts at commit pinned, with sqlglot Composer 4.0.
