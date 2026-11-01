"""Replace one code cell's whole source text of a notebook: _set_cell.py NB CELL_INDEX TEXTFILE."""
import json, sys
nb_path, index, text_path = sys.argv[1], int(sys.argv[2]), sys.argv[3]
raw = open(nb_path, encoding="utf-8").read()
nb = json.loads(raw)
text = open(text_path, encoding="utf-8").read()
lines = text.splitlines(keepends=True)
nb["cells"][index]["source"] = lines
out = json.dumps(nb, indent=1, ensure_ascii=False) + "\n"
open(nb_path, "w", encoding="utf-8", newline="\n").write(out)
print("cell", index, "set;", "same-indent" if raw.endswith("\n") else "no-trailing-newline in original")
