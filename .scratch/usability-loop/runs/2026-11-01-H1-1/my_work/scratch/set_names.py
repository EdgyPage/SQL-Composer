"""Fill the convert notebook's names cell and databases.py, as the user would by hand (my own helper)."""
import json, pathlib, re
root = pathlib.Path("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-H1-1/my_work/project")
nb_path = root / "admin/workflows/convert/convert.ipynb"
nb = json.loads(nb_path.read_text(encoding="utf-8"))
names_cell = nb["cells"][2]
new = [
    'NAME = "weekly"  # the batch\'s name, plain lowercase\n',
    'FILES = ["weekly.hql"]  # the scripts\' files, from this folder\n',
    "HIVE = None  # the Hive as text, or None to read FILES\n",
    'DATABASE = "mart"  # the database of a table the Hive names without one\n',
    "STAGING = {}  # left out: a temporary table is folded, any other kept\n",
]
assert "".join(names_cell["source"]).startswith("NAME = ''"), names_cell["source"][:1]
names_cell["source"] = new
nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
db = root / "admin/databases.py"
text = db.read_text(encoding="utf-8")
text = text.replace('"<DEV_DATABASE>"', '"mart_dev"').replace('"<PROD_DATABASE>"', '"team_prod"')
db.write_text(text, encoding="utf-8")
print(text)
