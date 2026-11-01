import sys
sys.path[:0] = [r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-W4-2\my_work\my_project",
                r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-W4-2"]
import os
os.chdir(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-W4-2\my_work\my_project")
from sqlglot_composer import project
print(project.do_next())
print(project.check())
