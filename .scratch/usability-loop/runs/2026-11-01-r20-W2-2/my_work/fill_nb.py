"""Replace text in a notebook: python fill_nb.py NB EDITS.py, where EDITS.py sets EDITS, a list
of (old, new, where) triples; where is "code" (code cells only) or "all". Every occurrence in
those cells is replaced; each old must occur at least once."""
import json
import runpy
import sys

path, edits_file = sys.argv[1], sys.argv[2]
edits = runpy.run_path(edits_file)["EDITS"]
with open(path, encoding="utf-8") as handle:
    nb = json.load(handle)
for old, new, where in edits:
    total = 0
    for cell in nb["cells"]:
        if where == "code" and cell["cell_type"] != "code":
            continue
        text = ''.join(cell["source"])
        if old in text:
            total += text.count(old)
            cell["source"] = text.replace(old, new).splitlines(keepends=True)
    if total == 0:
        sys.exit(f"{old!r} occurs nowhere in the {where} cells")
    print(f"{old!r}: {total} replaced")
with open(path, "w", encoding="utf-8", newline="\n") as handle:
    json.dump(nb, handle, indent=1, ensure_ascii=False)
    handle.write("\n")
