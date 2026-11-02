import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from sqlglot_composer import project
print(project.start())
