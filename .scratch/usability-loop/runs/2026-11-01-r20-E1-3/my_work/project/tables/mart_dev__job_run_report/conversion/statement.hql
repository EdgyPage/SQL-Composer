SELECT g.job_id,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(f.failed_runs, 0) AS failed_runs,
  a.avg_duration_mins
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) g
LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM ops.job_runs GROUP BY job_id) c
  ON g.job_id = c.job_id
LEFT JOIN (SELECT job_id, COUNT(*) AS failed_runs FROM ops.job_runs WHERE status = 'FAILED' GROUP BY job_id) f
  ON g.job_id = f.job_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_duration_mins FROM ops.job_runs GROUP BY job_id) a
  ON g.job_id = a.job_id;
