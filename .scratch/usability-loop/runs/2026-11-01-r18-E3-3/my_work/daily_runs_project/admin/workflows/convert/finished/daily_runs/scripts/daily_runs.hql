SELECT d.dt, COALESCE(c.runs, 0) AS runs, COALESCE(c.total_duration_mins, 0) AS total_duration_mins
FROM (SELECT '2026-09-23' AS dt UNION ALL SELECT '2026-09-24') d
LEFT JOIN (
  SELECT dt, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM ops.job_runs
  WHERE status IS NOT NULL AND (status <> 'TEST' OR status IS NULL)
  GROUP BY dt
) c
  ON d.dt = c.dt
