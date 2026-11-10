import sys
sys.path.append(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-09-W8-3")
from team_connection import conn
print(conn.query("SELECT dt, COUNT(*) AS n FROM mart.team_days GROUP BY dt ORDER BY dt"))
print(conn.query("SELECT * FROM mart.team_days WHERE dt BETWEEN '2026-09-14' AND '2026-09-20' LIMIT 3"))
