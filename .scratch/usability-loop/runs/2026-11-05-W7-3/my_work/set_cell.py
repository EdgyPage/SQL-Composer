"""Replace the source of the Nth code cell (counted from 1) of a notebook with a file's text."""
import json, sys
nb_path, n, text_path = sys.argv[1], int(sys.argv[2]), sys.argv[3]
nb = json.load(open(nb_path, encoding="utf-8"))
code = [c for c in nb["cells"] if c["cell_type"] == "code"]
text = open(text_path, encoding="utf-8").read()
lines = text.splitlines(keepends=True)
code[n - 1]["source"] = lines
with open(nb_path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")
print("set cell", n, "of", nb_path)
