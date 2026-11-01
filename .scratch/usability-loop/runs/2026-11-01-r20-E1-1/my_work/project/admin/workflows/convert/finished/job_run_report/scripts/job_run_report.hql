SELECT j.job_id,
  COALESCE(r.runs, 0) AS runs,
  COALESCE(r.failed_runs, 0) AS failed_runs,
  r.avg_duration_mins AS avg_duration_mins
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (
  SELECT job_id,
    COUNT(*) AS runs,
    COUNT(CASE WHEN status = 'FAILED' THEN 1 END) AS failed_runs,
    AVG(duration_mins) AS avg_duration_mins
  FROM ops.job_runs
  GROUP BY job_id
) r ON j.job_id = r.job_id
