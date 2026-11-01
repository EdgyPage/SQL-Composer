"""Replace the text of one code cell's first line-match in a notebook (my own helper)."""
import json
import sys

path, old, new = sys.argv[1], sys.argv[2], sys.argv[3]
nb = json.load(open(path, encoding="utf-8"))
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
if hits != 1:
    sys.exit(f"expected one cell, found {hits}")
with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")
print("ok")
