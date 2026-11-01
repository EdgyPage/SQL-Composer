import sys
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r19-E3-1\my_work\project")
from warehouse import query, execute
print(query("SHOW DATABASES"))
print(query("DESCRIBE ops.job_runs"))
