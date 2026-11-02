import json, sys
from pathlib import Path
path = Path(sys.argv[1])
raw = path.read_bytes().decode("utf-8")
nb = json.loads(raw)
cell = nb["cells"][2]
assert cell["cell_type"] == "code"
lines = [line for line in "".join(cell["source"]).splitlines()]
replacements = {
    "NAME = ''": 'NAME = "weekly"',
    "FILES = []": 'FILES = ["weekly.hql"]',
    "DATABASE = 'default'": "DATABASE = 'mart'",
    "RENAME = {}": 'RENAME = {"mart.team_fails": "team_fails", "mart.job_runs_counted": "job_runs_counted", "mart.job_fails_counted": "job_fails_counted"}',
}
done = set()
new = []
for line in lines:
    for old, rep in replacements.items():
        if line.startswith(old + "  #") or line == old:
            line = rep + line[len(old):]
            done.add(old)
            break
    new.append(line)
assert done == set(replacements), done
cell["source"] = [l + "\n" for l in new[:-1]] + [new[-1]]
out = json.dumps(nb, indent=1, ensure_ascii=False) + "\n"
path.write_bytes(out.replace("\n", "\r\n").encode("utf-8") if "\r\n" in raw else out.encode("utf-8"))
print("\n".join(new))
