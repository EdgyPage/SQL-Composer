import sys
sys.path.insert(0, ".")
import pandas as pd
pd.set_option("display.width", 200)
from warehouse import query
print(query("SHOW PARTITIONS mart_dev.runs_per_day"))
print(query("SELECT job_id, runs, dt FROM mart_dev.runs_per_day ORDER BY dt, job_id"))
print(query("SELECT COUNT(*) AS n FROM mart_dev.runs_per_day"))
