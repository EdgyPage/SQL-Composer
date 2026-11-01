import os, sys
root = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-W5-3\my_project"
os.chdir(os.path.join(root, "admin", "workflows", "change_a_saved_table"))
sys.path.insert(0, root)
from sqlglot_composer import project
print(project.check())
