import sys
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r19-E3-1\my_work\project")
import pandas as pd
pd.set_option("display.width", 200)
from warehouse import query, execute
print(query("DESCRIBE ops.job_runs").iloc[:, :2].to_string())
print(query("SHOW DATABASES").to_string())
