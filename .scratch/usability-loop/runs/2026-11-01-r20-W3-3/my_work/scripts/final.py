import sys
sys.path.append(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r20-W3-3\my_work\project")
from warehouse import query
import pandas as pd
pd.set_option("display.width", 200)
print(query("SHOW TABLES IN mart_dev"))
print(query("DESCRIBE mart_dev.failed_runs"))
print(query("SELECT * FROM mart_dev.failed_runs ORDER BY job_id"))
print(query("SELECT r.job_id, COUNT(*) AS fails FROM ops.job_runs r WHERE r.status = 'FAILED' GROUP BY r.job_id ORDER BY job_id"))
