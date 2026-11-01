## Q1

### Map

Sources
- `ops.job_runs`: the typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt. The Table job_runs is copied from ops.job_runs (its note in A1), so the source is written that way, as you asked. It has only typed columns and no query loads it, so it is a source, never a final.

Steps
- None. No query loads anything, and no Table's formula reads report.

Finals
- Table `report`, a summary, columns job_id, runs, failed_runs, avg_duration_mins. Its only typed column, job_id, is the one its COUNTIFS match on, so its final query is a GROUP BY of ops.job_runs with its typed job_ids (1, 2, 3) kept. It has no Total Row.

Not a source, step or final
- Parameters: an empty Table (name, value), read by no formula. It is left out of the Hive.
- Keys: an empty Table. No value is typed over a formula, so no Keys row is needed.

Values typed over a formula
- None.

Marks
- blank: none needed. The blank status in run 98 is read only inside the -IFS form (`status = 'FAILED'`), which skips it as written. avg_retry_secs is read by no formula.
- report.avg_duration_mins: AVERAGEIFS is AVG with no COALESCE, so a group with no row gives NULL where Excel gives #DIV/0!. Every group here has rows, so these values are unchanged.

Refusals
- None. Every formula converts.

Left alone
- The notes outside Tables: on Steps, at Parameters D1, Keys D1, report F1, and the A1 note on job_runs (used only for the source name).

`<...>` to fill in
- None. The source is ops.job_runs, as you asked.

### Hive

```sql
SELECT g.job_id,
  COALESCE(r.runs, 0) AS runs,
  COALESCE(f.failed_runs, 0) AS failed_runs,
  a.avg_duration_mins
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) g
LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM ops.job_runs GROUP BY job_id) r
  ON g.job_id = r.job_id
LEFT JOIN (SELECT job_id, COUNT(*) AS failed_runs FROM ops.job_runs WHERE status = 'FAILED' GROUP BY job_id) f
  ON g.job_id = f.job_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_duration_mins FROM ops.job_runs GROUP BY job_id) a
  ON g.job_id = a.job_id
```

### Next

Take out what you don't want, fill in each `<...>` (none here), save the query as report.hql, and run the convert Workflow on it as one batch (file 13). It writes and checks the Toolbox code.
