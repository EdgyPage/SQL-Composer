WITH CleanRuns AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM ops.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
)
SELECT d.dt, COALESCE(c.runs, 0) AS runs, COALESCE(s.total_duration_mins, 0) AS total_duration_mins
FROM (SELECT '2026-09-23' AS dt UNION ALL SELECT '2026-09-24') d
LEFT JOIN (SELECT dt, COUNT(*) AS runs FROM CleanRuns GROUP BY dt) c ON d.dt = c.dt
LEFT JOIN (SELECT dt, SUM(duration_mins) AS total_duration_mins FROM CleanRuns GROUP BY dt) s ON d.dt = s.dt
