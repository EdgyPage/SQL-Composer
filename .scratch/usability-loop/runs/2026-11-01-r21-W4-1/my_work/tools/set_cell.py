"""Set the source of one cell of a notebook, by its index among all cells, keeping the JSON layout."""
import json
import sys

path, index, text_file = sys.argv[1], int(sys.argv[2]), sys.argv[3]
raw = open(path, encoding="utf-8").read()
nb = json.loads(raw)
new_text = open(text_file, encoding="utf-8").read()
lines = new_text.splitlines(keepends=True)
nb["cells"][index]["source"] = lines
open(path, "w", encoding="utf-8", newline="\n").write(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
print("set cell", index, "of", path)
