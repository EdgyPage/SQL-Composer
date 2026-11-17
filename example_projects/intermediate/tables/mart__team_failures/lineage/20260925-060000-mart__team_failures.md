# Lineage: write_team_failures

Made by `export_lineage`. Each Statement has a section: what it reads and writes, its Run values and the Session settings sent before it, its Hive, then where each of its columns comes from.

Written as two files side by side, named alike: an HTML page, which draws the lineage, and a Markdown twin, the same sections as text, with no drawing. On the page, click a box, or press Tab until it is outlined and press Enter, to light up every box that feeds it and every box it feeds, and to open a panel on the right: for a calculated column, the column first, then the section of the Statement that makes it; for a table's column, the section of each Statement that writes or reads it. Escape, or a click on empty space, closes it.

## write_team_failures

It writes the Saved table mart.team_failures, replacing each partition its rows fill.

- Reads: ops.job_events, ops.job_owners
- Writes: mart.team_failures
- Session settings dynamic_partitions, sent before it: SET hive.exec.dynamic.partition=true; SET hive.exec.dynamic.partition.mode=nonstrict

### Hive as submitted

```sql
WITH ev AS (
  SELECT
    e.job_id,
    e.dt,
    e.event_type
  FROM ops.job_events AS e
  WHERE
    e.dt BETWEEN '2026-09-20' AND '2026-09-24'
    AND e.event_type IN ('start', 'retry', 'fail', 'finish')
), per_team AS (
  SELECT
    o.team,
    ev.dt,
    COUNT(*) AS events,
    SUM(CASE WHEN ev.event_type = 'fail' THEN 1 ELSE 0 END) AS fails
  FROM ev
  JOIN ops.job_owners AS o
    ON o.job_id = ev.job_id AND o.dt = ev.dt
  GROUP BY
    o.team,
    ev.dt
)
INSERT OVERWRITE TABLE mart.team_failures PARTITION(dt)
SELECT
  p.team,
  CASE p.team WHEN 'data' THEN 'Data platform' WHEN 'web' THEN 'Web' ELSE 'Other' END AS team_name,
  p.events,
  p.fails,
  p.dt
FROM per_team AS p
```

### Calculated columns

Every column that is calculated rather than copied, in the order it is calculated.

#### `per_team.events`

Calculated in **per_team** as `count_rows()`, which is `COUNT(*)`.

```text
per_team.events = count_rows()
└─ (no columns: it counts rows)
```

Rows that count:

- WHERE in ev: `all_of(between(e.dt, "2026-09-20", "2026-09-24"), is_in(e.event_type, ["start", "retry", "fail", "finish"]))`, which is `e.dt BETWEEN '2026-09-20' AND '2026-09-24' AND e.event_type IN ('start', 'retry', 'fail', 'finish')` (reads ops.job_events.dt, ops.job_events.event_type)
- JOIN ON in per_team: `all_of(equals(o.job_id, ev.job_id), equals(o.dt, ev.dt))`, which is `o.job_id = ev.job_id AND o.dt = ev.dt` (reads ops.job_events.dt, ops.job_events.job_id, ops.job_owners.dt, ops.job_owners.job_id)

One value for each different `o.team` and `ev.dt`.

#### `per_team.fails`

Calculated in **per_team** as `sum_of(if_else(equals(ev.event_type, "fail"), 1, 0))`, which is `SUM(CASE WHEN ev.event_type = 'fail' THEN 1 ELSE 0 END)`.

```text
per_team.fails = sum_of(if_else(equals(ev.event_type, "fail"), 1, 0))
└─ ev.event_type
   └─ ops.job_events.event_type  (string)
```

Rows that count:

- WHERE in ev: `all_of(between(e.dt, "2026-09-20", "2026-09-24"), is_in(e.event_type, ["start", "retry", "fail", "finish"]))`, which is `e.dt BETWEEN '2026-09-20' AND '2026-09-24' AND e.event_type IN ('start', 'retry', 'fail', 'finish')` (reads ops.job_events.dt, ops.job_events.event_type)
- JOIN ON in per_team: `all_of(equals(o.job_id, ev.job_id), equals(o.dt, ev.dt))`, which is `o.job_id = ev.job_id AND o.dt = ev.dt` (reads ops.job_events.dt, ops.job_events.job_id, ops.job_owners.dt, ops.job_owners.job_id)

One value for each different `o.team` and `ev.dt`.

#### `team_name`

Calculated in **write_team_failures** as `mapped(p.team, {"data": "Data platform", "web": "Web"}, otherwise="Other")`, which is `CASE p.team WHEN 'data' THEN 'Data platform' WHEN 'web' THEN 'Web' ELSE 'Other' END`.

```text
write_team_failures.team_name = mapped(p.team, {"data": "Data platform", "web": "Web"}, otherwise="Other")
└─ per_team.team
   └─ ops.job_owners.team  (string)
```

Rows that count:

- WHERE in ev: `all_of(between(e.dt, "2026-09-20", "2026-09-24"), is_in(e.event_type, ["start", "retry", "fail", "finish"]))`, which is `e.dt BETWEEN '2026-09-20' AND '2026-09-24' AND e.event_type IN ('start', 'retry', 'fail', 'finish')` (reads ops.job_events.dt, ops.job_events.event_type)
- JOIN ON in per_team: `all_of(equals(o.job_id, ev.job_id), equals(o.dt, ev.dt))`, which is `o.job_id = ev.job_id AND o.dt = ev.dt` (reads ops.job_events.dt, ops.job_events.job_id, ops.job_owners.dt, ops.job_owners.job_id)

### Copied columns

- `team` comes from per_team.team ← ops.job_owners.team
- `events` comes from per_team.events (calculated)
- `fails` comes from per_team.fails (calculated) ← ev.event_type ← ops.job_events.event_type
- `dt` comes from per_team.dt ← ev.dt ← ops.job_events.dt

### Keys

The columns that tell each step's rows apart, as the Toolbox works them out. A column in one is marked "in the Key" on its box in the drawing.

- derived('ev', ...): no Key the Toolbox can see, since e's rows are told apart by event_id, and SELECT leaves out e.event_id.
- derived('per_team', ...): Key (team, dt), since GROUP_BY makes one row for each team, dt.
- write_team_failures: Key (team, dt), since p's rows are told apart by team, dt.
- mart.team_failures' Key (team, dt) holds: each row written has its own.

---

Made by export_lineage on 2026-09-25 06:00, from your scripts at commit nogit, with sqlglot Composer 8.8.
