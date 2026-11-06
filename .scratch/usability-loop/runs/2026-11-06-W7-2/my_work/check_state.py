import sys
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-06-W7-2\my_work\team_project")
from sqlglot_composer import project, show_hive
print(project.check())
print("---- logic write Hive:")
t = project.load("mart_dev.run_log")
print(show_hive([t.create(), t.write()]))
print("---- seed Hive:")
print(show_hive(t.seed()))
from building_blocks.run_values import period_end
print("period_end() =", repr(period_end()))
