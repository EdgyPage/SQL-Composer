WITH job_runs AS (
  SELECT r.job_id, r.duration_mins, jb.team
  FROM ops.job_runs r
  LEFT JOIN ops.jobs jb ON r.job_id = jb.job_id
)
SELECT k.team, COALESCE(c.runs, 0) AS runs
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') k
LEFT JOIN (SELECT team, COUNT(*) AS runs FROM job_runs GROUP BY team) c
  ON k.team = c.team
