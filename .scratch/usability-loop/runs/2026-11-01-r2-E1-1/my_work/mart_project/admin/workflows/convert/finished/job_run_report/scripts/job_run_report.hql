WITH by_job AS (
  SELECT job_id, COUNT(*) AS runs, AVG(duration_mins) AS avg_duration_mins
  FROM ops.job_runs
  GROUP BY job_id
),
failed_by_job AS (
  SELECT job_id, COUNT(*) AS failed_runs
  FROM ops.job_runs
  WHERE status = 'FAILED'
  GROUP BY job_id
)
SELECT b.job_id,
  COALESCE(b.runs, 0) AS runs,
  COALESCE(f.failed_runs, 0) AS failed_runs,
  b.avg_duration_mins AS avg_duration_mins
FROM by_job b
LEFT JOIN failed_by_job f ON b.job_id = f.job_id
