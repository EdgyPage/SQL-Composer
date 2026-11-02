import json, sys
from pathlib import Path
nb_path = Path(sys.argv[1])
old, new = sys.argv[2], sys.argv[3]
nb = json.loads(nb_path.read_text(encoding="utf-8"))
hits = 0
for cell in nb["cells"]:
    if cell["cell_type"] != "markdown":
        continue
    text = "".join(cell["source"])
    if old in text:
        text = text.replace(old, new)
        cell["source"] = text.splitlines(keepends=True)
        hits += 1
assert hits == 1, hits
nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("replaced", hits)
