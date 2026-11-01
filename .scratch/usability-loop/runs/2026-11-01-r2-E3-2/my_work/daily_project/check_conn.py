from warehouse import query, execute

print(query("SELECT COUNT(*) AS n, COUNT(DISTINCT run_id) AS k, COUNT(DISTINCT dt) AS days FROM ops.job_runs"))
print(query("SELECT * FROM ops.job_runs LIMIT 5"))
