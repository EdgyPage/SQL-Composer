import json
path = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-W3-3/my_work/project/admin/workflows/new_table/new_table.ipynb"
text = open(path, encoding="utf-8").read()
old = 'DECISIONS = {}  # your answer to each open Decision'
new = ('DECISIONS = {\\"mart_dev.failed_runs\\": {\\"location\\": '
       '\\"/data/team/mart_dev.db/failed_runs\\"}}  # your answer to each open Decision')
assert text.count(old) == 1
text = text.replace(old, new)
nb = json.loads(text)  # still valid JSON
open(path, "w", encoding="utf-8", newline="").write(text)
print([c for c in nb["cells"] if "DECISIONS = " in "".join(c["source"])][0]["source"][0])
