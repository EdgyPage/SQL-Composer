from pathlib import Path
WORK = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-held-E4-1"
PROJECT = Path(WORK + "/my_work/costs_project")
p = PROJECT / "warehouse.py"
s = p.read_text(encoding="utf-8")
old = "import pandas as pd\n\nfrom sqlglot_composer import example_database\n"
new = ("import sys\n\nimport pandas as pd\n\n"
       'sys.path.append("' + WORK + '")\n'
       "from team_connection import conn  # the team's warehouse connection\n\n"
       "from sqlglot_composer import example_database  # noqa: E402\n")
assert s.count(old) == 1, "warehouse import block not found"
s = s.replace(old, new)
old2 = "conn = example_database\n"
assert s.count(old2) == 1, "conn line not found"
s = s.replace(old2, "")
p.write_text(s, encoding="utf-8")

d = PROJECT / "admin" / "databases.py"
t = d.read_text(encoding="utf-8")
t2 = t.replace('DEV = "<DEV_DATABASE>"', 'DEV = "mart_dev"').replace('PROD = "<PROD_DATABASE>"', 'PROD = "team_prod"')
assert t2 != t
d.write_text(t2, encoding="utf-8")
print(p.read_text(encoding="utf-8"))
print(d.read_text(encoding="utf-8"))
