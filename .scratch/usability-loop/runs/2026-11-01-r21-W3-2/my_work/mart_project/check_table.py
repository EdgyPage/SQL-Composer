from warehouse import query
print(query("SELECT * FROM mart_dev.failed_runs ORDER BY job_id"))
