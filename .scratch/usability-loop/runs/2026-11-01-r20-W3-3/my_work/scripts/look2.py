import sys
sys.path.append(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r20-W3-3\my_work\project")
from warehouse import query
import pandas as pd
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)
print(query("SELECT COUNT(*) AS n, COUNT(DISTINCT run_id) AS runs, COUNT(DISTINCT job_id) AS jobs FROM ops.job_runs"))
print(query("SELECT dt, COUNT(*) AS n, COUNT(DISTINCT run_id) AS runs FROM ops.job_runs GROUP BY dt ORDER BY dt"))
print(query("SELECT status, COUNT(*) AS n FROM ops.job_runs GROUP BY status"))
print(query("SELECT * FROM ops.job_runs LIMIT 12"))
