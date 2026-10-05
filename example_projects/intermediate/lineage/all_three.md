# Lineage: write_job_day_costs, write_job_day_facts, write_team_days

Made by `export_lineage`. The chart is written in Mermaid, which JupyterLab draws. Arrows run from where a value comes from to where it goes. A solid arrow carries a value. A dotted arrow carries a column into a condition, or runs from a condition to the step whose rows it decides (labelled "filters"). A dotted arrow labelled "day written" runs from a write's date bound to the day of the Saved table it writes.

## Graph

```mermaid
flowchart LR
  subgraph g0["ops.region_costs"]
    n0["ops.region_costs.job_id<br/><small>bigint</small>"]
    n2["ops.region_costs.dt<br/><small>string</small>"]
    n3["ops.region_costs.cost_cents<br/><small>bigint</small>"]
  end
  subgraph g1["costs_per_job_day"]
    n1["costs_per_job_day.job_id<br/><small>region_costs.job_id</small>"]
    n4["costs_per_job_day.cost_cents<br/><small>sum_of(region_costs.cost_cents)</small>"]
  end
  subgraph g2["filters on costs_per_job_day"]
    n5{{"WHERE in costs_per_job_day<br/><small>equals(region_costs.dt, datetime.date(2026,…</small>"}}
  end
  subgraph g3["write_job_day_costs"]
    n6["job_id<br/><small>costs_per_job_day.job_id</small>"]
    n7["cost_cents<br/><small>costs_per_job_day.cost_cents</small>"]
  end
  subgraph g4["mart.job_day_costs"]
    n8["mart.job_day_costs.job_id<br/><small>bigint</small>"]
    n9["mart.job_day_costs.cost_cents<br/><small>bigint</small>"]
    n10["mart.job_day_costs.dt<br/><small>string</small>"]
  end
  subgraph g5["ops.job_events"]
    n11["ops.job_events.job_id<br/><small>bigint</small>"]
    n13["ops.job_events.dt<br/><small>string</small>"]
    n16["ops.job_events.event_type<br/><small>string</small>"]
    n18["ops.job_events.minutes<br/><small>int</small>"]
  end
  subgraph g6["events_per_job_day"]
    n12["events_per_job_day.job_id<br/><small>job_events.job_id</small>"]
    n14["events_per_job_day.dt<br/><small>job_events.dt</small>"]
    n15["events_per_job_day.events<br/><small>count_rows()</small>"]
    n17["events_per_job_day.runs<br/><small>count_rows(where=equals(job_events.event_ty…</small>"]
    n19["events_per_job_day.minutes<br/><small>fill_null(sum_of(job_events.minutes, where=…</small>"]
  end
  subgraph g7["filters on events_per_job_day"]
    n20{{"WHERE in events_per_job_day<br/><small>equals(job_events.dt, datetime.date(2026, 9…</small>"}}
  end
  subgraph g8["write_job_day_facts"]
    n21["job_id<br/><small>events_per_job_day.job_id</small>"]
    n23["team<br/><small>job_owners.team</small>"]
    n24["events<br/><small>events_per_job_day.events</small>"]
    n25["runs<br/><small>events_per_job_day.runs</small>"]
    n26["minutes<br/><small>events_per_job_day.minutes</small>"]
  end
  subgraph g9["ops.job_owners"]
    n22["ops.job_owners.team<br/><small>string</small>"]
    n28["ops.job_owners.dt<br/><small>string</small>"]
    n29["ops.job_owners.job_id<br/><small>bigint</small>"]
  end
  subgraph g10["filters on write_job_day_facts"]
    n27{{"LEFT JOIN ON in write_job_day_facts<br/><small>all_of(equals(job_owners.job_id, events_per…</small>"}}
  end
  subgraph g11["mart.job_day_facts"]
    n30["mart.job_day_facts.job_id<br/><small>bigint</small>"]
    n31["mart.job_day_facts.team<br/><small>string</small>"]
    n32["mart.job_day_facts.events<br/><small>bigint</small>"]
    n33["mart.job_day_facts.runs<br/><small>bigint</small>"]
    n34["mart.job_day_facts.minutes<br/><small>bigint</small>"]
    n35["mart.job_day_facts.dt<br/><small>string</small>"]
  end
  subgraph g12["write_team_days"]
    n36["team<br/><small>job_day_facts.team</small>"]
    n37["events<br/><small>sum_of(job_day_facts.events)</small>"]
    n38["runs<br/><small>sum_of(job_day_facts.runs)</small>"]
    n39["minutes<br/><small>sum_of(job_day_facts.minutes)</small>"]
    n40["cost_cents<br/><small>sum_of(job_day_costs.cost_cents)</small>"]
  end
  subgraph g13["filters on write_team_days"]
    n41{{"WHERE in write_team_days<br/><small>equals(job_day_facts.dt, datetime.date(2026…</small>"}}
    n42{{"LEFT JOIN ON in write_team_days<br/><small>all_of(equals(job_day_costs.job_id, job_day…</small>"}}
  end
  subgraph g14["mart.team_days"]
    n43["mart.team_days.team<br/><small>string</small>"]
    n44["mart.team_days.events<br/><small>bigint</small>"]
    n45["mart.team_days.runs<br/><small>bigint</small>"]
    n46["mart.team_days.minutes<br/><small>bigint</small>"]
    n47["mart.team_days.cost_cents<br/><small>bigint</small>"]
    n48["mart.team_days.dt<br/><small>string</small>"]
  end
  n0 --> n1
  n3 --> n4
  n2 -.-> n5
  n1 --> n6
  n4 --> n7
  n6 --> n8
  n7 --> n9
  n5 -.->|day written| n10
  n11 --> n12
  n13 --> n14
  n16 --> n17
  n18 --> n19
  n16 --> n19
  n13 -.-> n20
  n12 --> n21
  n22 --> n23
  n15 --> n24
  n17 --> n25
  n19 --> n26
  n28 -.-> n27
  n29 -.-> n27
  n12 -.-> n27
  n14 -.-> n27
  n21 --> n30
  n23 --> n31
  n24 --> n32
  n25 --> n33
  n26 --> n34
  n20 -.->|day written| n35
  n31 --> n36
  n32 --> n37
  n33 --> n38
  n34 --> n39
  n9 --> n40
  n35 -.-> n41
  n10 -.-> n42
  n8 -.-> n42
  n30 -.-> n42
  n35 -.-> n42
  n36 --> n43
  n37 --> n44
  n38 --> n45
  n39 --> n46
  n40 --> n47
  n41 -.->|day written| n48
  n5 -.->|filters| g1
  n20 -.->|filters| g6
  n27 -.->|filters| g8
  n41 -.->|filters| g12
  n42 -.->|filters| g12
```

## write_job_day_costs

It writes the Saved table mart.job_day_costs, one day at a time.

### Calculated columns

Every column that is calculated rather than copied, in the order it is calculated.

#### `costs_per_job_day.cost_cents`

Calculated in **costs_per_job_day** as `sum_of(region_costs.cost_cents)`, which is `SUM(region_costs.cost_cents)`.

```text
costs_per_job_day.cost_cents = sum_of(region_costs.cost_cents)
└─ ops.region_costs.cost_cents  (bigint)
```

Rows that count:
- WHERE in costs_per_job_day: `equals(region_costs.dt, datetime.date(2026, 9, 24))`, which is `region_costs.dt = '20260924'` (reads ops.region_costs.dt)

One value for each different `region_costs.job_id` and `region_costs.dt`.

### Copied columns

| Output | Comes from |
| --- | --- |
| `job_id` | costs_per_job_day.job_id ← ops.region_costs.job_id |
| `cost_cents` | costs_per_job_day.cost_cents (calculated) ← ops.region_costs.cost_cents |

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

Calculated in **events_per_job_day** as `fill_null(sum_of(job_events.minutes, where=is_in(job_events.event_type, ["finish", "fail"])), 0)`, which is `COALESCE(SUM(CASE WHEN job_events.event_type IN ('finish', 'fail') THEN job_events.minutes END), 0)`.

```text
events_per_job_day.minutes = fill_null(sum_of(job_events.minutes, where=is_in(job_events.event_type, ["finish", "fail"])), 0)
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
    COALESCE(
      SUM(
        CASE WHEN job_events.event_type IN ('finish', 'fail') THEN job_events.minutes END
      ),
      0
    ) AS minutes
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

It reads the Saved table mart.job_day_costs, written by write_job_day_costs above. It reads the Saved table mart.job_day_facts, written by write_job_day_facts above. It writes the Saved table mart.team_days, one day at a time.

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
- LEFT JOIN ON in write_job_day_facts: `all_of(equals(job_owners.job_id, events_per_job_day.job_id), equals(job_owners.dt, events_per_job_day.dt), between(job_owners.dt, "2026-09-24", "2026-09-24"))`, which is `job_owners.job_id = events_per_job_day.job_id AND job_owners.dt = events_per_job_day.dt AND job_owners.dt BETWEEN '2026-09-24' AND '2026-09-24'` (reads ops.job_events.dt, ops.job_events.job_id, ops.job_owners.dt, ops.job_owners.job_id)
- WHERE in write_team_days: `equals(job_day_facts.dt, datetime.date(2026, 9, 24))`, which is `job_day_facts.dt = '2026-09-24'` (reads mart.job_day_facts.dt)
- LEFT JOIN ON in write_team_days: `all_of(equals(job_day_costs.job_id, job_day_facts.job_id), equals(job_day_costs.dt, job_day_facts.dt), between(job_day_costs.dt, "2026-09-24", "2026-09-24"))`, which is `job_day_costs.job_id = job_day_facts.job_id AND job_day_costs.dt = job_day_facts.dt AND job_day_costs.dt BETWEEN '2026-09-24' AND '2026-09-24'` (reads mart.job_day_costs.dt, mart.job_day_costs.job_id, mart.job_day_facts.dt, mart.job_day_facts.job_id)

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
- LEFT JOIN ON in write_job_day_facts: `all_of(equals(job_owners.job_id, events_per_job_day.job_id), equals(job_owners.dt, events_per_job_day.dt), between(job_owners.dt, "2026-09-24", "2026-09-24"))`, which is `job_owners.job_id = events_per_job_day.job_id AND job_owners.dt = events_per_job_day.dt AND job_owners.dt BETWEEN '2026-09-24' AND '2026-09-24'` (reads ops.job_events.dt, ops.job_events.job_id, ops.job_owners.dt, ops.job_owners.job_id)
- WHERE in write_team_days: `equals(job_day_facts.dt, datetime.date(2026, 9, 24))`, which is `job_day_facts.dt = '2026-09-24'` (reads mart.job_day_facts.dt)
- LEFT JOIN ON in write_team_days: `all_of(equals(job_day_costs.job_id, job_day_facts.job_id), equals(job_day_costs.dt, job_day_facts.dt), between(job_day_costs.dt, "2026-09-24", "2026-09-24"))`, which is `job_day_costs.job_id = job_day_facts.job_id AND job_day_costs.dt = job_day_facts.dt AND job_day_costs.dt BETWEEN '2026-09-24' AND '2026-09-24'` (reads mart.job_day_costs.dt, mart.job_day_costs.job_id, mart.job_day_facts.dt, mart.job_day_facts.job_id)

One value for each different `job_day_facts.dt` and `job_day_facts.team`.

#### `minutes`

Calculated in **write_team_days** as `sum_of(job_day_facts.minutes)`, which is `SUM(job_day_facts.minutes)`.

```text
write_team_days.minutes = sum_of(job_day_facts.minutes)
└─ mart.job_day_facts.minutes  (bigint)
   └─ write_job_day_facts.minutes
      └─ events_per_job_day.minutes = fill_null(sum_of(job_events.minutes, where=is_in(job_events.event_type, ["finish", "fail"])), 0)
         ├─ ops.job_events.minutes  (int)
         └─ ops.job_events.event_type  (string)
```

Rows that count:
- LEFT JOIN ON in write_job_day_facts: `all_of(equals(job_owners.job_id, events_per_job_day.job_id), equals(job_owners.dt, events_per_job_day.dt), between(job_owners.dt, "2026-09-24", "2026-09-24"))`, which is `job_owners.job_id = events_per_job_day.job_id AND job_owners.dt = events_per_job_day.dt AND job_owners.dt BETWEEN '2026-09-24' AND '2026-09-24'` (reads ops.job_events.dt, ops.job_events.job_id, ops.job_owners.dt, ops.job_owners.job_id)
- WHERE in write_team_days: `equals(job_day_facts.dt, datetime.date(2026, 9, 24))`, which is `job_day_facts.dt = '2026-09-24'` (reads mart.job_day_facts.dt)
- LEFT JOIN ON in write_team_days: `all_of(equals(job_day_costs.job_id, job_day_facts.job_id), equals(job_day_costs.dt, job_day_facts.dt), between(job_day_costs.dt, "2026-09-24", "2026-09-24"))`, which is `job_day_costs.job_id = job_day_facts.job_id AND job_day_costs.dt = job_day_facts.dt AND job_day_costs.dt BETWEEN '2026-09-24' AND '2026-09-24'` (reads mart.job_day_costs.dt, mart.job_day_costs.job_id, mart.job_day_facts.dt, mart.job_day_facts.job_id)

One value for each different `job_day_facts.dt` and `job_day_facts.team`.

#### `cost_cents`

Calculated in **write_team_days** as `sum_of(job_day_costs.cost_cents)`, which is `SUM(job_day_costs.cost_cents)`.

```text
write_team_days.cost_cents = sum_of(job_day_costs.cost_cents)
└─ mart.job_day_costs.cost_cents  (bigint)
   └─ write_job_day_costs.cost_cents
      └─ costs_per_job_day.cost_cents = sum_of(region_costs.cost_cents)
         └─ ops.region_costs.cost_cents  (bigint)
```

Rows that count:
- LEFT JOIN ON in write_job_day_facts: `all_of(equals(job_owners.job_id, events_per_job_day.job_id), equals(job_owners.dt, events_per_job_day.dt), between(job_owners.dt, "2026-09-24", "2026-09-24"))`, which is `job_owners.job_id = events_per_job_day.job_id AND job_owners.dt = events_per_job_day.dt AND job_owners.dt BETWEEN '2026-09-24' AND '2026-09-24'` (reads ops.job_events.dt, ops.job_events.job_id, ops.job_owners.dt, ops.job_owners.job_id)
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

Made by export_lineage on 2026-09-25 06:00, from your scripts at commit pinned, with sqlglot Composer 3.2.
