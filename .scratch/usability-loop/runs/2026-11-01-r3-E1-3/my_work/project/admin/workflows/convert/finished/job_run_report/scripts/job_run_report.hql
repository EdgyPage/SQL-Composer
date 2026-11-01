-- Report of the run_report_formula.xlsx workbook: one row per job, its runs, failed runs and average minutes.
SELECT job_id,
  COALESCE(COUNT(*), 0) AS runs,
  COALESCE(COUNT(CASE WHEN status = 'FAILED' THEN 1 END), 0) AS failed_runs,
  AVG(duration_mins) AS avg_duration_mins
FROM ops.job_runs
GROUP BY job_id
