"""Replace the lines of one code cell's assignments in a notebook, by line prefix.

usage: set_cell.py NOTEBOOK CELL_INDEX 'PREFIX=>NEW LINE' ...
Each argument replaces the first line that starts with PREFIX (the text before '=>').
"""
import json
import sys

nb_path, index = sys.argv[1], int(sys.argv[2])
nb = json.load(open(nb_path, encoding="utf-8"))
lines = "".join(nb["cells"][index]["source"]).split("\n")
for arg in sys.argv[3:]:
    prefix, new = arg.split("=>", 1)
    hits = [i for i, line in enumerate(lines) if line.startswith(prefix)]
    assert len(hits) == 1, (prefix, hits)
    lines[hits[0]] = new
text = "\n".join(lines)
nb["cells"][index]["source"] = text.splitlines(keepends=True)
json.dump(nb, open(nb_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
open(nb_path, "a", encoding="utf-8").write("\n")
print("\n".join(lines))
