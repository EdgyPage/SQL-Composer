from pathlib import Path
RUN = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-E2-3"
proj = Path(RUN) / "my_work" / "project"
w = proj / "warehouse.py"
s = w.read_text(encoding="utf-8")
old = "conn = example_database\n"
assert s.count(old) == 1
new = ("import sys\n"
       "sys.path.append(r\"" + RUN + "\")\n"
       "from team_connection import conn  # my team's warehouse connection\n")
w.write_text(s.replace(old, new), encoding="utf-8")
d = proj / "admin" / "databases.py"
t = d.read_text(encoding="utf-8")
t = t.replace('DEV = "<DEV_DATABASE>"', 'DEV = "mart_dev"').replace('PROD = "<PROD_DATABASE>"', 'PROD = "team_prod"')
d.write_text(t, encoding="utf-8")
