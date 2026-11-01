import sys
sys.path.insert(0, ".")
sys.path.append("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r19-E2-3")
from team_connection import conn
for q in ["SHOW DATABASES", "SHOW TABLES IN ops", "SHOW TABLES IN mart_dev", "SHOW TABLES IN team_prod"]:
    try:
        print(q, "->"); print(conn.query(q))
    except Exception as e:
        print("ERR", q, type(e).__name__, e)
