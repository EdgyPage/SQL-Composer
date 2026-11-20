# Lineage: write_job_events_checks

Made by `export_lineage`. Each Statement has a section: what it reads and writes, its Run values and the Session settings sent before it, its Hive, then where each of its columns comes from.

Written as two files side by side, named alike: an HTML page, which draws the lineage, and a Markdown twin, the same sections as text, with no drawing. On the page, click a box, or press Tab until it is outlined and press Enter, to light up every box that feeds it and every box it feeds, and to open a panel on the right: for a calculated column, the column first, then the section of the Statement that makes it; for a table's column, the section of each Statement that writes or reads it. Escape, or a click on empty space, closes it.

## write_job_events_checks

It writes the Saved table mart.job_events_checks, replacing each partition its rows fill.

- Reads: ops.job_events
- Writes: mart.job_events_checks
- Session settings dynamic_partitions, sent before it: SET hive.exec.dynamic.partition=true; SET hive.exec.dynamic.partition.mode=nonstrict

### Hive as submitted

```sql
INSERT OVERWRITE TABLE mart.job_events_checks PARTITION(dt)
SELECT
  COUNT(*) AS row_count,
  job_events.dt
FROM ops.job_events AS job_events
WHERE
  job_events.dt = '2026-09-24'
GROUP BY
  job_events.dt
```

### Calculated columns

Every column that is calculated rather than copied, in the order it is calculated.

#### `row_count`

Calculated in **write_job_events_checks** as `count_rows()`, which is `COUNT(*)`.

```text
write_job_events_checks.row_count = count_rows()
└─ (no columns: it counts rows)
```

Rows that count:

- WHERE in write_job_events_checks: `equals(job_events.dt, "2026-09-24")`, which is `job_events.dt = '2026-09-24'` (reads ops.job_events.dt)

One value for each different `job_events.dt`.

### Copied columns

- `dt` comes from ops.job_events.dt

### Keys

The columns that tell each step's rows apart, as the Toolbox works them out. A column in one is marked "in the Key" on its box in the drawing.

- write_job_events_checks: one row, so it needs no Key: GROUP_BY makes one row for each dt, with dt held to one value.
- mart.job_events_checks' Key (dt) holds: each row written has its own.

---

Made by export_lineage on 2026-09-25 06:00, from your scripts at commit nogit, with sqlglot Composer 8.9.
