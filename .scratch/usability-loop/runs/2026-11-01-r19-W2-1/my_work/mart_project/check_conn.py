from warehouse import query, execute
print(query("SHOW DATABASES"))
print(query("SHOW TABLES IN mart_dev"))
print(query("SHOW PARTITIONS ops.job_runs").tail(5))
