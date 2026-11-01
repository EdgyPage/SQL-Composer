WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.team
  FROM ops.job_runs r
  LEFT JOIN ops.jobs j ON r.job_id = j.job_id
),
per_team AS (
  SELECT team, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM job_runs
  GROUP BY team
)
SELECT t.team,
  COALESCE(p.runs, 0) AS runs,
  COALESCE(p.total_duration_mins, 0) AS total_duration_mins
FROM (
  SELECT 'data' AS team
  UNION ALL SELECT 'finance'
  UNION ALL SELECT 'web'
) t
LEFT JOIN per_team p ON t.team = p.team;
