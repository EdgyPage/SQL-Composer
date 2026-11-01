WITH CleanRuns AS (
  SELECT dt, duration_mins
  FROM ops.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
)
SELECT dt, COUNT(*) AS runs, COALESCE(SUM(duration_mins), 0) AS total_duration_mins
FROM CleanRuns
GROUP BY dt;
