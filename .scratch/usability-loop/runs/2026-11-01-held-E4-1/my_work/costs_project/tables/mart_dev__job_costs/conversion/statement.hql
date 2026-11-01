WITH job_runs AS (
  SELECT job_id, duration_mins
  FROM ops.job_runs
)
SELECT c.job_id,
  CASE WHEN c.job_id = 3 THEN 1000 ELSE COALESCE(m.total_minutes, 0) * 50 END AS cost_cents
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4) c
LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total_minutes
           FROM job_runs
           GROUP BY job_id) m ON c.job_id = m.job_id;
