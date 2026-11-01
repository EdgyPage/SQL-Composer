import json
from pathlib import Path

path = Path("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-W5-2/my_project/admin/workflows/change_a_saved_table/change_a_saved_table.ipynb")
nb = json.loads(path.read_text(encoding="utf-8"))

def replace_in_cell(old, new):
    hits = 0
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        text = "".join(cell["source"])
        if old in text:
            text = text.replace(old, new)
            lines = text.splitlines(keepends=True)
            cell["source"] = lines
            hits += 1
    assert hits == 1, (old, hits)

replace_in_cell("from sqlglot_composer import admin, hive_settings, project, run_execute, run_query, show_hive",
                "from sqlglot_composer import admin, equals, hive_settings, project, run_execute, run_query, show_hive")
replace_in_cell("TABLE = ''  # the Saved table", 'TABLE = "mart_dev.runs_per_day"  # the Saved table')
replace_in_cell("change = admin.drop_partitions(table, where=...)",
                'change = admin.drop_partitions(table, where=equals(table.dt, "2026-09-24"))')

path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("saved")
