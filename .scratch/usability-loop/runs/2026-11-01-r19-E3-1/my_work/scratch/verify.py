import sys
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r19-E3-1\my_work\project")
import pandas as pd
pd.set_option("display.width", 200)
from warehouse import query, execute
from sqlglot_composer import project
print(query("SELECT * FROM mart_dev.daily_runs ORDER BY dt").to_string())
print(query("SHOW DATABASES").to_string())
print(project.check())
