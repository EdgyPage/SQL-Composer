import sys
sys.path.append(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-E4-1")
from team_connection import conn
for sql in ["SHOW DATABASES", "SHOW TABLES IN ops", "SHOW TABLES IN mart_dev", "SHOW TABLES IN team_prod"]:
    try:
        print("##", sql)
        print(conn.query(sql))
    except Exception as e:
        print("ERR", type(e).__name__, e)
