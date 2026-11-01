import sys
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r20-W2-3\my_work")
from warehouse import query
import pandas as pd
pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 20)
print(query("SELECT COUNT(*) AS n, COUNT(DISTINCT run_id) AS runs_ids, COUNT(DISTINCT job_id) AS jobs, MIN(dt) AS mind, MAX(dt) AS maxd FROM ops.job_runs"))
print(query("SELECT dt, job_id, COUNT(*) AS runs FROM ops.job_runs WHERE dt BETWEEN '2026-09-23' AND '2026-09-24' GROUP BY dt, job_id ORDER BY dt, job_id"))
print(query("SELECT dt, COUNT(*) AS n, COUNT(DISTINCT run_id) AS d FROM ops.job_runs GROUP BY dt ORDER BY dt"))
print(query("SELECT run_id, job_id, status, dt FROM ops.job_runs WHERE dt BETWEEN '2026-09-23' AND '2026-09-24' ORDER BY dt, job_id, run_id"))
print(query("SHOW TBLPROPERTIES ops.job_runs"))
print(query("SELECT status, COUNT(*) FROM ops.job_runs GROUP BY status"))
