import os
import sys
os.chdir(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-W5-2\my_project\admin\workflows\change_a_saved_table")
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-W5-2\my_project")
from sqlglot_composer import project

print(project.check())
