import sys
sys.path.append(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-E4-1")
from team_connection import conn
for sql in ["DESCRIBE ops.jobs", "DESCRIBE ops.job_runs", "SELECT * FROM ops.jobs", "SELECT * FROM ops.job_runs"]:
    try:
        print("##", sql)
        print(conn.query(sql).to_string())
    except Exception as e:
        print("ERR", type(e).__name__, e)
