# Lineage: write_daily_job_runs

Made by `export_lineage`. Each Statement has a section: what it reads and writes, its Run values and the Session settings sent before it, its Hive, then where each of its columns comes from.

Written as two files side by side, named alike: an HTML page, which draws the lineage, and a Markdown twin, the same sections as text, with no drawing. On the page, click a box, or press Tab until it is outlined and press Enter, to light up every box that feeds it and every box it feeds, and to open a panel on the right: for a calculated column, the column first, then the section of the Statement that makes it; for a table's column, the section of each Statement that writes or reads it. Escape, or a click on empty space, closes it.

## write_daily_job_runs

It writes the Saved table mart.daily_job_runs, replacing each partition its rows fill.

- Reads: ops.job_runs
- Writes: mart.daily_job_runs
- Session settings dynamic_partitions, sent before it: SET hive.exec.dynamic.partition=true; SET hive.exec.dynamic.partition.mode=nonstrict

### Hive as submitted

```sql
WITH runs_per_job AS (
  SELECT
    job_runs.job_id,
    job_runs.dt,
    COUNT(*) AS runs,
    COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END) AS failed_runs,
    SUM(job_runs.duration_mins) AS minutes
  FROM ops.job_runs AS job_runs
  WHERE
    job_runs.dt = '2026-09-24'
  GROUP BY
    job_runs.job_id,
    job_runs.dt
)
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt)
SELECT
  runs_per_job.job_id,
  runs_per_job.runs,
  runs_per_job.failed_runs,
  runs_per_job.minutes,
  runs_per_job.dt
FROM runs_per_job
```

### Calculated columns

Every column that is calculated rather than copied, in the order it is calculated.

#### `runs_per_job.runs`

Calculated in **runs_per_job** as `count_rows()`, which is `COUNT(*)`.

```text
runs_per_job.runs = count_rows()
└─ (no columns: it counts rows)
```

Rows that count:

- WHERE in runs_per_job: `equals(job_runs.dt, "2026-09-24")`, which is `job_runs.dt = '2026-09-24'` (reads ops.job_runs.dt)

One value for each different `job_runs.job_id` and `job_runs.dt`.

#### `runs_per_job.failed_runs`

Calculated in **runs_per_job** as `count_rows(where=equals(job_runs.status, "FAILED"))`, which is `COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END)`.

```text
runs_per_job.failed_runs = count_rows(where=equals(job_runs.status, "FAILED"))
└─ ops.job_runs.status  (string)
```

Rows that count:

- WHERE in runs_per_job: `equals(job_runs.dt, "2026-09-24")`, which is `job_runs.dt = '2026-09-24'` (reads ops.job_runs.dt)

One value for each different `job_runs.job_id` and `job_runs.dt`.

#### `runs_per_job.minutes`

Calculated in **runs_per_job** as `sum_of(job_runs.duration_mins)`, which is `SUM(job_runs.duration_mins)`.

```text
runs_per_job.minutes = sum_of(job_runs.duration_mins)
└─ ops.job_runs.duration_mins  (int)
```

Rows that count:

- WHERE in runs_per_job: `equals(job_runs.dt, "2026-09-24")`, which is `job_runs.dt = '2026-09-24'` (reads ops.job_runs.dt)

One value for each different `job_runs.job_id` and `job_runs.dt`.

### Copied columns

- `job_id` comes from runs_per_job.job_id ← ops.job_runs.job_id
- `runs` comes from runs_per_job.runs (calculated)
- `failed_runs` comes from runs_per_job.failed_runs (calculated) ← ops.job_runs.status
- `minutes` comes from runs_per_job.minutes (calculated) ← ops.job_runs.duration_mins
- `dt` comes from runs_per_job.dt ← ops.job_runs.dt

### Keys

The columns that tell each step's rows apart, as the Toolbox works them out. A column in one is marked "in the Key" on its box in the drawing.

- derived('runs_per_job', ...): Key (job_id), since GROUP_BY makes one row for each job_id, dt, with dt held to one value.
- write_daily_job_runs: Key (job_id), since runs_per_job's rows are told apart by job_id.
- mart.daily_job_runs' Key (job_id, dt) holds: each row written has its own.

---

Made by export_lineage on 2026-09-25 06:00, from your scripts at commit nogit, with sqlglot Composer 8.8.
