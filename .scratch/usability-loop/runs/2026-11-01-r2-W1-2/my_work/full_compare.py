import sys
sys.path.insert(0, "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r2-W1-2")
from team_connection import conn
a = conn.query("SELECT team, fails, dt FROM mart.team_fails").sort_values(["dt", "team"]).reset_index(drop=True)
b = conn.query("SELECT team, fails, dt FROM mart_dev.team_fails").sort_values(["dt", "team"]).reset_index(drop=True)
print("original rows:", len(a), " dev rows:", len(b))
print("identical:", a.astype(str).equals(b.astype(str)))
print(a)
print(b)
