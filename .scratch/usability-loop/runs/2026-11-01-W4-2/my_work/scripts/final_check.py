import sys, os
sys.path[:0] = [r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-W4-2\my_work\my_project",
                r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-W4-2"]
os.chdir(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-W4-2\my_work\my_project")
from references import ops
from admin import databases
print(ops.jobs, ops.run_alerts, sep="\n")
print("DEV", databases.DEV, "PROD", databases.PROD)
print(sorted(os.listdir("references")))
print(sorted(os.listdir("admin")))
