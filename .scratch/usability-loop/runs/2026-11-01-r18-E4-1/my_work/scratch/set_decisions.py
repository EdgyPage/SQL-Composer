import json
from pathlib import Path
nb_path = Path("project/admin/workflows/convert/convert.ipynb")
nb = json.loads(nb_path.read_text(encoding="utf-8"))
code = [c for c in nb["cells"] if c["cell_type"] == "code"]
dec = code[2]
dec["source"] = [
    "DECISIONS = {\n",
    '    "mart_dev.job_costs": {"location": "/data/team/mart_dev.db/job_costs"},\n',
    '    "mart_dev.team_runs": {"location": "/data/team/mart_dev.db/team_runs"},\n',
    "}\n",
]
nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("".join(dec["source"]))
