exec(open(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-W1-3\my_work\_scripts\header.py").read())
from warehouse import query
import pandas as pd
pd.set_option("display.width", 200)
for sql in ["SELECT * FROM ops.job_owners LIMIT 3", "SELECT * FROM mart.team_fails LIMIT 3", "SELECT * FROM ops.job_runs LIMIT 3"]:
    try:
        print(sql); print(query(sql))
    except Exception as e:
        print("ERR", type(e).__name__, str(e)[:700])
