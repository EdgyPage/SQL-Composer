WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.team
  FROM ops.job_runs r
  LEFT JOIN ops.jobs j ON r.job_id = j.job_id
),
team_keys AS (
  SELECT 'data' AS team
  UNION ALL SELECT 'finance'
  UNION ALL SELECT 'web'
)
SELECT k.team,
  COUNT(jr.run_id) AS runs,
  COALESCE(SUM(jr.duration_mins), 0) AS total_duration_mins
FROM team_keys k
LEFT JOIN job_runs jr ON jr.team = k.team
GROUP BY k.team
