"""Replace the source of one code cell of a notebook, found by a line it holds."""
import json
import sys


def set_cell(path, must_contain, new_source):
    with open(path, encoding="utf-8") as f:
        nb = json.load(f)
    hits = [c for c in nb["cells"] if c["cell_type"] == "code" and must_contain in "".join(c["source"])]
    if len(hits) != 1:
        raise SystemExit(f"{len(hits)} code cells hold {must_contain!r} in {path}; need exactly 1")
    lines = new_source.splitlines(keepends=True)
    hits[0]["source"] = lines
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"set the cell holding {must_contain!r} in {path}")


if __name__ == "__main__":
    notebook, marker, source_file = sys.argv[1:4]
    with open(source_file, encoding="utf-8") as f:
        set_cell(notebook, marker, f.read())
