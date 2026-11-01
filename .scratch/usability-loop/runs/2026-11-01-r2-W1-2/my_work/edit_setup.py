from pathlib import Path

base = Path("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r2-W1-2/my_work/team_project")
p = base / "admin" / "databases.py"
t = p.read_text(encoding="utf-8")
t = t.replace('DEV = "<DEV_DATABASE>"  # such as "mart_dev"', 'DEV = "mart_dev"  # such as "mart_dev"')
t = t.replace('PROD = "<PROD_DATABASE>"  # such as "mart"', 'PROD = "team_prod"  # such as "mart"')
p.write_text(t, encoding="utf-8")

w = base / "warehouse.py"
t = w.read_text(encoding="utf-8")
old_import = "from sqlglot_composer import example_database\n"
assert old_import in t
new_import = (
    "import sys\n"
    'sys.path.append("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r2-W1-2")\n'
    "from team_connection import conn\n"
    "\n"
    "from sqlglot_composer import example_database\n"
)
t = t.replace(old_import, new_import, 1)
assert "conn = example_database\n" in t
t = t.replace("conn = example_database\n", "", 1)
w.write_text(t, encoding="utf-8")
