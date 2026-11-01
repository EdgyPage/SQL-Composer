import sys
sys.path.append(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r20-W3-3\my_work\project")
from warehouse import query
import pandas as pd
pd.set_option("display.width", 200)
print(query("SHOW DATABASES"))
print(query("SHOW TABLES IN mart_dev"))
print(query("SHOW TABLES IN team_prod"))
print(query("SHOW TABLES IN ops"))
print(query("SELECT r.job_id, COUNT(*) AS fails FROM ops.job_runs r WHERE r.status = 'FAILED' GROUP BY r.job_id"))
