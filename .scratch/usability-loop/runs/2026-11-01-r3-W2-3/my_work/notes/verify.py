import sys
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r3-W2-3\my_work")
import pandas as pd
pd.set_option("display.width", 200)
from warehouse import query
print(query("SELECT job_id, runs, dt FROM mart_dev.runs_per_day ORDER BY dt, job_id"))
print(query("SELECT COUNT(*) AS n, COUNT(DISTINCT dt) AS days FROM mart_dev.runs_per_day"))
