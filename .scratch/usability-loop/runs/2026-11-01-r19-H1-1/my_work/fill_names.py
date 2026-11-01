import json, re
from pathlib import Path

path = Path(__file__).resolve().parent / "admin" / "workflows" / "convert" / "convert.ipynb"
nb = json.loads(path.read_text(encoding="utf-8"))
cell = nb["cells"][2]
text = "".join(cell["source"])
values = {
    "NAME": "'team_weekly'",
    "FILES": "['weekly.hql']",
    "RENAME": '{"mart.team_fails": "team_fails", "mart.job_runs_counted": "job_runs_counted", "mart.job_fails_counted": "job_fails_counted"}',
}
out = []
for line in text.split("\n"):
    for name, value in values.items():
        if line.startswith(name + " = "):
            comment = line.split("  #", 1)[1] if "  #" in line else ""
            line = f"{name} = {value}  #{comment}"
    out.append(line)
new_text = "\n".join(out)
cell["source"] = new_text.splitlines(keepends=True)
path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(new_text)
