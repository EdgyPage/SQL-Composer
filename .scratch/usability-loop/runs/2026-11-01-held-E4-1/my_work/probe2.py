import sys, os
ROOT = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-held-E4-1"
sys.path.insert(0, ROOT + "/my_work/costs_project")
os.chdir(ROOT + "/my_work/costs_project")
from warehouse import query, execute
print(query("SHOW TABLES IN mart_dev"))
print(query("SHOW TABLES IN team_prod"))
for t in ["mart_dev.job_costs", "mart_dev.team_runs"]:
    try:
        print(t); print(query("DESCRIBE " + t))
    except Exception as e:
        print("ERR", str(e)[:300])
