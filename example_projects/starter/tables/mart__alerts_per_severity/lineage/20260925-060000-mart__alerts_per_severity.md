# Lineage: write_alerts_per_severity

Made by `export_lineage`. Each Statement has a section: what it reads and writes, its Run values and the Session settings sent before it, its Hive, then where each of its columns comes from.

Written as two files side by side, named alike: an HTML page, which draws the lineage, and a Markdown twin, the same sections as text, with no drawing. On the page, click a box, or press Tab until it is outlined and press Enter, to light up every box that feeds it and every box it feeds, and to open a panel on the right: for a calculated column, the column first, then the section of the Statement that makes it; for a table's column, the section of each Statement that writes or reads it. Escape, or a click on empty space, closes it.

## write_alerts_per_severity

It writes the Saved table mart.alerts_per_severity, replacing each partition its rows fill.

- Reads: ops.run_alerts
- Writes: mart.alerts_per_severity
- Session settings dynamic_partitions, sent before it: SET hive.exec.dynamic.partition=true; SET hive.exec.dynamic.partition.mode=nonstrict

### Hive as submitted

```sql
INSERT OVERWRITE TABLE mart.alerts_per_severity PARTITION(dt)
SELECT
  run_alerts.severity,
  COUNT(*) AS alerts,
  run_alerts.dt
FROM ops.run_alerts AS run_alerts
WHERE
  run_alerts.dt = '2026-09-24'
GROUP BY
  run_alerts.severity,
  run_alerts.dt
```

### Calculated columns

Every column that is calculated rather than copied, in the order it is calculated.

#### `alerts`

Calculated in **write_alerts_per_severity** as `count_rows()`, which is `COUNT(*)`.

```text
write_alerts_per_severity.alerts = count_rows()
└─ (no columns: it counts rows)
```

Rows that count:

- WHERE in write_alerts_per_severity: `equals(run_alerts.dt, "2026-09-24")`, which is `run_alerts.dt = '2026-09-24'` (reads ops.run_alerts.dt)

One value for each different `run_alerts.severity` and `run_alerts.dt`.

### Copied columns

- `severity` comes from ops.run_alerts.severity
- `dt` comes from ops.run_alerts.dt

### Keys

The columns that tell each step's rows apart, as the Toolbox works them out. A column in one is marked "in the Key" on its box in the drawing.

- write_alerts_per_severity: Key (severity), since GROUP_BY makes one row for each severity, dt, with dt held to one value.
- mart.alerts_per_severity's Key (severity, dt) holds: each row written has its own.

---

Made by export_lineage on 2026-09-25 06:00, from your scripts at commit nogit, with sqlglot Composer 8.10.
