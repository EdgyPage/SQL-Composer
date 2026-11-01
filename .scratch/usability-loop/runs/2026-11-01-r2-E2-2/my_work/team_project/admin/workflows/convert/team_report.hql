WITH job_runs AS (
  SELECT r.duration_mins, j.team
  FROM ops.job_runs r
  LEFT JOIN ops.jobs j ON r.job_id = j.job_id
),
listed AS (
  SELECT 'data' AS team
  UNION ALL SELECT 'finance'
  UNION ALL SELECT 'web'
),
summary AS (
  SELECT team, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM job_runs
  GROUP BY team
)
SELECT l.team,
  COALESCE(s.runs, 0) AS runs,
  COALESCE(s.total_duration_mins, 0) AS total_duration_mins
FROM listed l
LEFT JOIN summary s ON l.team = s.team
