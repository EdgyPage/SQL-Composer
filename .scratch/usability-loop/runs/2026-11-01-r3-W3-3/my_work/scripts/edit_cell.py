"""Replace one exact text in a notebook's code cells, keeping the notebook's JSON format."""
import json
import sys
from pathlib import Path

path, old, new = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
nb = json.loads(path.read_text(encoding="utf-8"))
hits = 0
for cell in nb["cells"]:
    text = "".join(cell["source"])
    if old in text:
        hits += 1
        text = text.replace(old, new)
        lines = text.splitlines(keepends=True)
        cell["source"] = lines
if hits != 1:
    sys.exit(f"expected one cell with the text, found {hits}")
path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("edited", path.name)
