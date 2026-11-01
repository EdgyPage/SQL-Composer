"""Fill in one code cell's line of a Workflow notebook: set_names.py NOTEBOOK OLD NEW."""
import json
import sys

path, old, new = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path, encoding="utf-8") as f:
    nb = json.load(f)
hits = 0
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    cell["source"] = [line.replace(old, new) if old in line else line for line in cell["source"]]
    hits += sum(1 for line in cell["source"] if new in line)
with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")
print("lines now holding the new text:", hits)
