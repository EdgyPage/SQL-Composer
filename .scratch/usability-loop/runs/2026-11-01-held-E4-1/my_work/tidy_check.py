import sys, os
from pathlib import Path
ROOT = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-held-E4-1"
p = Path(ROOT + "/my_work/costs_project/warehouse.py")
s = p.read_text(encoding="utf-8")
s2 = s.replace("from sqlglot_composer import example_database  # noqa: E402\n\n", "")
s2 = s2.replace("# Your connection to the warehouse. At work, replace example_database with your own, such as\n"
                "# conn = your_library.connect(...): its query(sql) gives back a DataFrame, and its\n"
                "# execute(sql) runs Hive that changes something.\n", "")
assert s2 != s
p.write_text(s2, encoding="utf-8")
sys.path.insert(0, ROOT + "/my_work/costs_project")
os.chdir(ROOT + "/my_work/costs_project")
from sqlglot_composer import project
print(project.check())
