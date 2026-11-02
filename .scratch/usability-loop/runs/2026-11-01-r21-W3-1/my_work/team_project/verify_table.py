from warehouse import query

print(query("SELECT COUNT(*) AS n FROM mart_dev.failed_runs"))
