"""Replace the first line of a notebook's code cells that starts with PREFIX, as the file's JSON source list."""
import json
import sys
from pathlib import Path

path, prefix, new_line = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
nb = json.loads(path.read_text(encoding="utf-8"))
hits = 0
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    lines = cell["source"]
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lines[i] = new_line + ("\n" if line.endswith("\n") else "")
            hits += 1
            break
if hits != 1:
    sys.exit(f"expected one line starting with {prefix!r}, found {hits}")
path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("set", hits)
