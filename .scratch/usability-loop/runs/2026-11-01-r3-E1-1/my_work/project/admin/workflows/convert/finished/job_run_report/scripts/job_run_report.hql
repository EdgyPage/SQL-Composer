SELECT r.job_id,
  COALESCE(COUNT(*), 0) AS runs,
  COALESCE(COUNT(CASE WHEN r.status = 'FAILED' THEN 1 END), 0) AS failed_runs,
  AVG(r.duration_mins) AS avg_duration_mins
FROM ops.job_runs r
GROUP BY r.job_id
