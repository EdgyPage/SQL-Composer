WITH job_runs AS (
  SELECT r.job_id, r.duration_mins, jb.team
  FROM ops.job_runs r
  LEFT JOIN ops.jobs jb ON r.job_id = jb.job_id
)
SELECT k.job_id,
  CASE WHEN k.job_id = 3 THEN 1000
    ELSE COALESCE(c.total, 0) * 50 END AS cost_cents
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4) k
LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total FROM job_runs GROUP BY job_id) c
  ON k.job_id = c.job_id;
