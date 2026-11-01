import os
import sys

PROJECT = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-W1-1\my_work\team_project"
os.chdir(PROJECT)
sys.path.insert(0, PROJECT)

import pandas as pd
pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 120)

from sqlglot_composer import project
from warehouse import query

info = query("DESCRIBE FORMATTED mart_dev.team_fails")
print(info[info["col_name"].astype(str).str.contains("Location|Table Type|Partition", case=False, regex=True)])
print(project.check())
