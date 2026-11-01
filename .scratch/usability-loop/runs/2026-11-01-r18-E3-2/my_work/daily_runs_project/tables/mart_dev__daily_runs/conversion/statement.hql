WITH job_runs AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt,
    IF(COALESCE(status, '') <> '' AND COALESCE(status, '') <> 'TEST', 1, 0) AS kept
  FROM ops.job_runs
)
SELECT d.dt, COALESCE(c.runs, 0) AS runs, COALESCE(c.total_duration_mins, 0) AS total_duration_mins
FROM (SELECT '2026-09-23' AS dt UNION ALL SELECT '2026-09-24') d
LEFT JOIN (
  SELECT dt, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM job_runs
  WHERE kept = 1
  GROUP BY dt
) c
  ON d.dt = c.dt;
