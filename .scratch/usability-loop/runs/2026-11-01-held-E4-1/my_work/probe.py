import sys
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-held-E4-1\my_work\costs_project")
import os
os.chdir(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-held-E4-1\my_work\costs_project")
from warehouse import query, execute, conn
print(type(conn))
for sql in ["SHOW DATABASES", "SHOW TABLES IN ops", "SHOW TABLES IN mart_dev"]:
    try:
        print(sql); print(query(sql))
    except Exception as e:
        print("ERR", type(e).__name__, str(e)[:500])
