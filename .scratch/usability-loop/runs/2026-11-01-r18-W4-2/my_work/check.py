import sys, os
P = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-W4-2\my_work\my_project"
sys.path.insert(0, P)
os.chdir(P)
from sqlglot_composer import project
print(project.check())
