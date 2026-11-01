import sys
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r19-E3-1\my_work\project")
from references.mart_dev__daily_runs import daily_runs
from sqlglot_composer import project
from sqlglot_composer import run_execute
print(daily_runs.create() if callable(getattr(daily_runs,'create',None)) else 'no create on Table')
