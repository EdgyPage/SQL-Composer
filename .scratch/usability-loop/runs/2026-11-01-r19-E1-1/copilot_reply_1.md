
**Map**

- **Sources**: `job_runs`, the Table on the Runs sheet, read as `<database>.job_runs` (the whole table, never its sample rows). Its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt.
- **Steps**: none. The workbook has no Power Query, and no Table's formula reads another Table as a step.
- **Finals**: `run_report`, the Table on the Report sheet, as a summary. Its only typed column, job_id, is the one its COUNTIFS and AVERAGEIFS match on, so its typed groups 1, 2 and 3 are typed in and `job_runs` is read. Columns: job_id, runs, failed_runs, avg_duration_mins.
- **Total Rows**: none.
- **Parameters** and **Keys**: both are empty, so neither is a source, step or final; left out.
- **Typed over a formula**: none. Keys is empty, and every formula cell on the Report sheet is still a formula.
- **Marks**: avg_duration_mins, an AVG with no COALESCE. Where a job has no run, Hive gives NULL where AVERAGEIFS gives #DIV/0!. All three jobs have runs, so no row shows this.
- **Refusals**: none.
- **Left alone**: the text on the Steps sheet; the note in Runs A1 ("Copied from ops.job_runs in our warehouse."); the notes in Report F1, Parameters D1 and Keys D1, each outside its Table. No charts or PivotTables. The blank status on run 98 is skipped by failed_runs' condition, as Excel skips it, so it needs no mark.
- **To fill in**: `<database>`, three times in the Hive. Table and column names are plain, so nothing else needs filling. Runs A1 names ops as where job_runs came from, which is likely the database.

**Hive**

```sql
SELECT j.job_id, COALESCE(r.runs, 0) AS runs, COALESCE(f.failed_runs, 0) AS failed_runs, a.avg_duration_mins
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) r
  ON j.job_id = r.job_id
LEFT JOIN (SELECT job_id, COUNT(*) AS failed_runs FROM <database>.job_runs WHERE status = 'FAILED' GROUP BY job_id) f
  ON j.job_id = f.job_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_duration_mins FROM <database>.job_runs GROUP BY job_id) a
  ON j.job_id = a.job_id
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
