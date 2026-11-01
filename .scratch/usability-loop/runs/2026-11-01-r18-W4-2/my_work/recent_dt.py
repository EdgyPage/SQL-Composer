import sys, os
P = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-W4-2\my_work\my_project"
sys.path.insert(0, P)
os.chdir(P)
from sqlglot_composer import (statement, SELECT, FROM, WHERE, GROUP_BY, ORDER_BY, AS,
                              count_rows, last_n_days, run_query, show_hive, descending)
from references.ops__run_alerts import run_alerts
from warehouse import query

for days in (30, 365):
    recent = statement(
        SELECT(run_alerts.dt, AS(count_rows(), "alerts")),
        FROM(run_alerts),
        WHERE(last_n_days(run_alerts.dt, days)),
        GROUP_BY(run_alerts.dt),
    )
    print(show_hive(recent))
    print(run_query(recent, query).sort_values('dt', ascending=False))
    print("=====")
