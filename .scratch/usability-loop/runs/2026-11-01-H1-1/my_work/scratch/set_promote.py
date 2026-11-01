"""Fill the promote notebook's names cell with the three dev tables (my own helper)."""
import json, pathlib
nb_path = pathlib.Path("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-H1-1/my_work/project/admin/workflows/promote/promote.ipynb")
nb = json.loads(nb_path.read_text(encoding="utf-8"))
cell = nb["cells"][2]
assert "TABLES = []" in "".join(cell["source"])
cell["source"] = ['TABLES = ["mart_dev.team_fails", "mart_dev.job_runs_counted", "mart_dev.job_fails_counted"]  '
                  "# the dev tables, by their names in your Dev Database\n"]
nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("".join(cell["source"]))
