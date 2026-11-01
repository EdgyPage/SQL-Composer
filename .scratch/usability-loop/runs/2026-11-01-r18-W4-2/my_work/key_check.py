import sys, os
P = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-W4-2\my_work\my_project"
sys.path.insert(0, P)
os.chdir(P)
from sqlglot_composer import check_key, equals
from references.ops__run_alerts import run_alerts
from warehouse import query
for day in ("2026-09-23", "2026-09-24"):
    print(check_key(run_alerts, query=query, where=equals(run_alerts.dt, day)))
