import sys, os
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-W2-1\my_work")
os.chdir(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-W2-1\my_work")
from warehouse import query, execute
import pandas as pd
pd.set_option("display.width", 200)
print(query("SELECT COUNT(*) AS n, COUNT(DISTINCT run_id) AS distinct_run_ids, COUNT(DISTINCT dt) AS days FROM ops.job_runs"))
print(query("SELECT dt, job_id, COUNT(*) AS runs FROM ops.job_runs WHERE dt BETWEEN '2026-09-23' AND '2026-09-24' GROUP BY dt, job_id ORDER BY dt, job_id"))
print(query("SELECT dt, COUNT(*) AS n FROM ops.job_runs GROUP BY dt ORDER BY dt"))
