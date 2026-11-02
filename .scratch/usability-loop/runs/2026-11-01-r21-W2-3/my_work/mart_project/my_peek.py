import sys
sys.path.insert(0, ".")
import pandas as pd
pd.set_option("display.width", 200)
from warehouse import query
print(query("SHOW PARTITIONS ops.job_runs"))
print(query("SELECT * FROM ops.job_runs LIMIT 5"))
print(query("SELECT COUNT(*) AS n, COUNT(DISTINCT run_id) AS distinct_runs FROM ops.job_runs"))
print(query("SELECT dt, job_id, COUNT(*) AS runs FROM ops.job_runs WHERE dt BETWEEN '2026-09-23' AND '2026-09-24' GROUP BY dt, job_id ORDER BY dt, job_id"))
