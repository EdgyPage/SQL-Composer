import sys, os
ROOT = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r19-W5-2"
sys.path.insert(0, os.path.join(ROOT, "my_project"))
os.chdir(os.path.join(ROOT, "my_project"))
from sqlglot_composer import project
print(project.check())
from warehouse import query
print(query("SHOW PARTITIONS mart_dev.runs_per_day"))
