import os, sys
os.chdir(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-E2-3\my_work\project")
sys.path.insert(0, os.getcwd())
from sqlglot_composer import project
print(project.check())
