"""Replace one exact text in one cell of a notebook, once: _edit_cell.py NB INDEX OLDFILE NEWFILE."""
import json, sys
nb_path, index, old_path, new_path = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
raw = open(nb_path, encoding="utf-8").read()
nb = json.loads(raw)
old = open(old_path, encoding="utf-8").read()
new = open(new_path, encoding="utf-8").read()
text = "".join(nb["cells"][index]["source"])
count = text.count(old)
assert count == 1, f"expected one match, found {count}"
text = text.replace(old, new)
nb["cells"][index]["source"] = text.splitlines(keepends=True)
open(nb_path, "w", encoding="utf-8", newline="\n").write(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
print("cell", index, "edited")
