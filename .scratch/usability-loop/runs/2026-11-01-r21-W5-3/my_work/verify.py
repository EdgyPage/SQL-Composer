import sys
from pathlib import Path

project_dir = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-W5-3\my_project")
sys.path.insert(0, str(project_dir))
import os
os.chdir(project_dir)

from sqlglot_composer import project
from warehouse import query

print(query("SHOW PARTITIONS mart_dev.runs_per_day"))
print(project.check())
