WITH CleanRuns AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM ops.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
)
SELECT dt,
  COALESCE(COUNT(*), 0) AS runs,
  COALESCE(SUM(duration_mins), 0) AS total_duration_mins
FROM CleanRuns
GROUP BY dt;
