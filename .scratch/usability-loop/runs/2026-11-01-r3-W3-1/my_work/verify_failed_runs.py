from warehouse import query

print(query("SELECT * FROM mart_dev.failed_runs ORDER BY job_id"))
print(query("SELECT r.job_id, COUNT(*) AS fails FROM ops.job_runs r WHERE r.status = 'FAILED' GROUP BY r.job_id ORDER BY job_id"))
