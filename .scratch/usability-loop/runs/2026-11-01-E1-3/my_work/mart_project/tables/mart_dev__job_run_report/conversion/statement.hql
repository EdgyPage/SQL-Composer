SELECT job_id,
  COUNT(*) AS runs,
  COALESCE(SUM(CASE WHEN status = 'FAILED' THEN 1 END), 0) AS failed_runs,
  AVG(duration_mins) AS avg_duration_mins
FROM ops.job_runs
GROUP BY job_id;
