import sys, pathlib, os
here = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(here.parents[1]))
sys.path.insert(0, str(here))
os.chdir(here)
from sqlglot_composer import *
from sqlglot_composer import project
from warehouse import query, execute
t = project.load("mart_dev.runs_per_day")
print(show_hive([t.create(), t.write()]))
print("---- preview rows")
print(run_query(t.preview(), query))
