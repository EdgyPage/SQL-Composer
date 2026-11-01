WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.team
  FROM ops.job_runs r
  LEFT JOIN ops.jobs j ON r.job_id = j.job_id
)
SELECT t.team,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(c.total_duration_mins, 0) AS total_duration_mins
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') t
LEFT JOIN (
  SELECT team, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM job_runs
  GROUP BY team
) c
  ON t.team = c.team;
