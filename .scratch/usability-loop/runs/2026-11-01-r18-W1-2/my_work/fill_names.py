"""Fill in the convert notebook's names cell and databases.py, then save them."""
import json
from pathlib import Path

project = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-W1-2\my_work\team_project")

db = project / "admin" / "databases.py"
text = db.read_text(encoding="utf-8")
text = text.replace('DEV = "<DEV_DATABASE>"', 'DEV = "mart_dev"')
text = text.replace('PROD = "<PROD_DATABASE>"', 'PROD = "team_prod"')
db.write_text(text, encoding="utf-8")

nb_path = project / "admin" / "workflows" / "convert" / "convert.ipynb"
nb = json.loads(nb_path.read_text(encoding="utf-8"))
names = {
    "NAME = ''": "NAME = 'weekly_fails'",
    "FILES = []": "FILES = ['weekly_fails.hql']",
    "RENAME = {}": "RENAME = {'mart.team_fails': 'team_fails'}",
}
done = set()
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    if src.startswith("NAME = ''"):
        lines = src.split("\n")
        out = []
        for line in lines:
            for old, new in names.items():
                if line.startswith(old):
                    line = new + line[len(old):]
                    done.add(old)
            out.append(line)
        cell["source"] = "\n".join(out).splitlines(keepends=True)
assert done == set(names), done
nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(db.read_text(encoding="utf-8"))
for cell in nb["cells"]:
    if cell["cell_type"] == "code" and "NAME = " in "".join(cell["source"]):
        print("".join(cell["source"]))
