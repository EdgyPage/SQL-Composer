WITH runs AS (
  SELECT r.job_id, r.duration_mins
  FROM ops.job_runs r
),
run_totals AS (
  SELECT job_id, SUM(duration_mins) AS total_mins
  FROM runs
  GROUP BY job_id
)
SELECT j.job_id,
  CASE WHEN j.job_id = 3 THEN 1000
    ELSE COALESCE(t.total_mins, 0) * 50
  END AS cost_cents
FROM ops.jobs j
LEFT JOIN run_totals t ON j.job_id = t.job_id
