"""Replace one line of a notebook's code cell, keeping the rest of the notebook as it was."""
import json
import sys

path, old, new = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path, encoding="utf-8") as f:
    nb = json.load(f)
hits = 0
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    text = "".join(cell["source"])
    if old in text:
        text = text.replace(old, new, 1)
        lines = text.splitlines(keepends=True)
        cell["source"] = lines
        hits += 1
if hits != 1:
    sys.exit(f"expected one cell with {old!r}, found {hits}")
with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")
print("ok")
