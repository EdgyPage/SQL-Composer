from pathlib import Path
base = Path("project")
p = base / "warehouse.py"
s = p.read_text(encoding="utf-8")
old_import = "from sqlglot_composer import example_database\n"
new_import = (
    "import sys\n"
    'sys.path.append("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r18-E4-1")\n'
    "from team_connection import conn  # the team's warehouse connection\n"
)
assert s.count(old_import) == 1
s = s.replace(old_import, new_import)
old_conn = "conn = example_database\n"
assert s.count(old_conn) == 1
s = s.replace(old_conn, "")
p.write_text(s, encoding="utf-8")
d = base / "admin" / "databases.py"
t = d.read_text(encoding="utf-8")
t = t.replace('DEV = "<DEV_DATABASE>"', 'DEV = "mart_dev"').replace('PROD = "<PROD_DATABASE>"', 'PROD = "team_prod"')
d.write_text(t, encoding="utf-8")
