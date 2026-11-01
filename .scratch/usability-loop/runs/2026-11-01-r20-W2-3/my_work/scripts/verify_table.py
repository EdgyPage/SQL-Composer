import sys
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r20-W2-3\my_work")
from warehouse import query
import pandas as pd
pd.set_option("display.width", 200)
print(query("SELECT job_id, runs, dt FROM mart_dev.runs_per_day ORDER BY dt, job_id"))
