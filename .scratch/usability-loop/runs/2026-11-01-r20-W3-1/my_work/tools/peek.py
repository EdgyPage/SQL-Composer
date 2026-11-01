import sys
sys.path.insert(0, "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r20-W3-1/my_work/project")
from warehouse import query
for hive in ["SHOW TABLES IN mart_dev", "SHOW TABLES IN team_prod"]:
    try:
        print(hive, "\n", query(hive))
    except Exception as error:
        print(hive, "failed:", type(error).__name__, error)
