"""Replace one line of a code cell in a notebook: python set_names.py NB OLD_PREFIX NEW_LINE."""
import json
import sys

path, prefix, new_line = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path, encoding="utf-8") as handle:
    nb = json.load(handle)
hits = 0
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    lines = cell["source"]
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lines[i] = new_line + "\n" if not new_line.endswith("\n") else new_line
            hits += 1
if hits != 1:
    sys.exit(f"expected one line starting {prefix!r}, found {hits}")
with open(path, "w", encoding="utf-8", newline="\n") as handle:
    json.dump(nb, handle, indent=1, ensure_ascii=False)
    handle.write("\n")
print("set", hits)
