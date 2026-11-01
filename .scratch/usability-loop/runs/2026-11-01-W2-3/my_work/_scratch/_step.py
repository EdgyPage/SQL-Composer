import sys, pathlib, os
here = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(here.parents[1]))
sys.path.insert(0, str(here))
os.chdir(here)
from sqlglot_composer import *
from sqlglot_composer import project
from warehouse import query, execute
print("---- do_next")
print(project.do_next())
print("---- check")
print(project.check())
