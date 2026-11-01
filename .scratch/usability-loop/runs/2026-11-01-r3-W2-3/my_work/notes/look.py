import sys
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r3-W2-3\my_work")
import pandas as pd
pd.set_option("display.width", 200)
from sqlglot_composer import first_look, run_query, show_hive
from warehouse import query
from references.ops__job_runs import job_runs
s = first_look(job_runs)
print(show_hive(s))
print(run_query(s, query))
