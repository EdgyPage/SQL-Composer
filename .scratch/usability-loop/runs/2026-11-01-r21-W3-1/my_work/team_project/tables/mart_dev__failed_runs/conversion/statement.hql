SELECT r.job_id, COUNT(*) AS fails
FROM ops.job_runs r
WHERE r.status = 'FAILED'
GROUP BY r.job_id;
