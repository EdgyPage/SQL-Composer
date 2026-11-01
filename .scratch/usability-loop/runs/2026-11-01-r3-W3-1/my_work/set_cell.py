"""Replace the text of the first code cell whose source starts with PREFIX, in a notebook."""
import json
import sys

path, prefix, new_text_file = sys.argv[1], sys.argv[2], sys.argv[3]
new_text = open(new_text_file, encoding="utf-8").read()
nb = json.load(open(path, encoding="utf-8"))
hits = [c for c in nb["cells"] if c["cell_type"] == "code" and "".join(c["source"]).startswith(prefix)]
assert len(hits) == 1, f"{len(hits)} cells start with {prefix!r}"
lines = new_text.splitlines(keepends=True)
hits[0]["source"] = lines
with open(path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")
print("set", path)
