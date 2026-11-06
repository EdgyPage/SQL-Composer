import sys
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-06-H1-1\my_work\team_project")
from warehouse import query, execute
for sql in ["SHOW DATABASES", "SHOW TABLES IN mart", "SHOW TABLES IN ops", "SHOW TABLES IN team_prod", "SHOW TABLES IN mart_dev", "DESCRIBE mart.team_fails", "SHOW PARTITIONS mart.team_fails"]:
    try:
        print("##", sql); print(query(sql))
    except Exception as e:
        print("ERR", type(e).__name__, e)
