import os
os.chdir(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-W2-1\my_work")
import sys
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-W2-1\my_work")
from sqlglot_composer import project
print(project.start())
