# Lineage: write_job_day_facts

Made by `export_lineage`. Each Statement has a section: what it reads and writes, its Run values and the Session settings sent before it, its Hive, then where each of its columns comes from.

Written as two files side by side, named alike: an HTML page, which draws the lineage, and a Markdown twin, the same sections as text, with no drawing. On the page, click a box, or press Tab until it is outlined and press Enter, to light up every box that feeds it and every box it feeds, and to open a panel on the right: for a calculated column, the column first, then the section of the Statement that makes it; for a table's column, the section of each Statement that writes or reads it. Escape, or a click on empty space, closes it.

## write_job_day_facts

It writes the Saved table mart.job_day_facts, replacing each partition its rows fill.

- Reads: ops.job_events, ops.job_owners
- Writes: mart.job_day_facts
- Session settings dynamic_partitions, sent before it: SET hive.exec.dynamic.partition=true; SET hive.exec.dynamic.partition.mode=nonstrict

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

- `job_id` comes from events_per_job.job_id ← ops.job_events.job_id
- `team` comes from ops.job_owners.team
- `events` comes from events_per_job.events (calculated)
- `runs` comes from events_per_job.runs (calculated) ← ops.job_events.event_type
- `minutes` comes from events_per_job.minutes (calculated) ← ops.job_events.minutes
- `dt` comes from events_per_job.dt ← ops.job_events.dt

### Keys

The columns that tell each step's rows apart, as the Toolbox works them out. A column in one is marked "in the Key" on its box in the drawing.

- derived('events_per_job', ...): Key (job_id, dt), since GROUP_BY makes one row for each job_id, dt.
- write_job_day_facts: Key (job_id, dt), since events_per_job's rows are told apart by job_id, dt.
- mart.job_day_facts' Key (job_id, dt) holds: each row written has its own.

---

Made by export_lineage on 2026-09-25 06:00, from your scripts at commit nogit, with sqlglot Composer 8.10.
