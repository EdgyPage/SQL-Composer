import json
from pathlib import Path

NB = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-W1-3\my_work\team_project\admin\workflows\convert\convert.ipynb")
nb = json.loads(NB.read_text(encoding="utf-8"))
names = '''NAME = "team_fails"  # the batch's name, plain lowercase, such as "weekly" (or, for the last cell alone, a list of batches converted already)
FILES = ["weekly_fails.hql"]  # the scripts' files, from this folder, such as ["daily.hql"], or [] to read HIVE
HIVE = None  # the Hive as text, such as """SELECT ...""", or None to read FILES
DATABASE = 'default'  # the database of a table the Hive names without one
RENAME = {"mart.team_fails": "team_fails"}  # a name of your own for a table's copy in dev, by the table's full name: mart_dev.team_fails
STAGING = {}  # each staging table convert names, kept or folded, such as {"ops_reports.failed": "keep"}: left out, a temporary or DROPped one is folded, any other kept
'''
done = 0
for cell in nb["cells"]:
    if cell["cell_type"] == "code" and "".join(cell["source"]).startswith("NAME = ''"):
        cell["source"] = names.splitlines(keepends=True)
        done += 1
assert done == 1, done
NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("names cell filled")
