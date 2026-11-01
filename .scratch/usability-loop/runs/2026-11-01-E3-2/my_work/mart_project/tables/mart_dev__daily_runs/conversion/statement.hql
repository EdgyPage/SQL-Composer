WITH CleanRuns AS (
  SELECT dt, duration_mins
  FROM ops.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
)
SELECT
  dt,
  COUNT(*) AS runs,
  SUM(duration_mins) AS total_duration_mins
FROM CleanRuns
GROUP BY dt;
