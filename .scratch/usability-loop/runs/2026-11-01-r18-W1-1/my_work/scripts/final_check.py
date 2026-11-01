import os
import sys

PROJECT = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-W1-1\my_work\team_project"
os.chdir(PROJECT)
sys.path.insert(0, PROJECT)

import pandas as pd
pd.set_option("display.width", 200)

from warehouse import query

print(query("SELECT team, fails, dt FROM mart_dev.team_fails ORDER BY dt, team"))
print(query("SELECT team, fails, dt FROM mart.team_fails ORDER BY dt, team"))
print(query("SELECT COUNT(*) AS n FROM mart_dev.team_fails"))
