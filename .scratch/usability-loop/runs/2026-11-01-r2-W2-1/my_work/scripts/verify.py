import sys, os
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-W2-1\my_work")
os.chdir(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-W2-1\my_work")
from warehouse import query
import pandas as pd
pd.set_option("display.width", 200)
print(query("SELECT * FROM mart_dev.runs_per_day WHERE dt BETWEEN '2026-09-23' AND '2026-09-24' ORDER BY dt, job_id"))
print(query("SHOW PARTITIONS mart_dev.runs_per_day"))
print(query("DESCRIBE FORMATTED mart_dev.runs_per_day"))
