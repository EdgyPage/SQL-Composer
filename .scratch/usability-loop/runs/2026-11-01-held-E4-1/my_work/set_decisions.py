import json
from pathlib import Path
nb_path = Path("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-held-E4-1/my_work/costs_project/admin/workflows/convert/convert.ipynb")
nb = json.loads(nb_path.read_text(encoding="utf-8"))
hits = 0
for cell in nb["cells"]:
    if cell["cell_type"] == "code" and "".join(cell["source"]).startswith("DECISIONS = {}"):
        cell["source"] = [
            '# Each Decision answered from the workbook: job_costs has one row per job_id, as its Keys row\n',
            '# says; team_runs has one row per team. Each folder is the team\'s own, as the task names it.\n',
            'DECISIONS = {\n',
            '    "mart_dev.job_costs": {"location": "/data/team/mart_dev.db/job_costs", "key": ["job_id"]},\n',
            '    "mart_dev.team_runs": {"location": "/data/team/mart_dev.db/team_runs", "key": ["team"]},\n',
            '}\n',
        ]
        hits += 1
assert hits == 1, hits
nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("decisions cell set")
