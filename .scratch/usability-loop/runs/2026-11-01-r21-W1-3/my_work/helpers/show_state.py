import sys
sys.path.insert(0, ".")
from sqlglot_composer import project, show_hive
print(project.check())
print("-----")
print(show_hive(project.load("mart_dev.team_fails").create()))
