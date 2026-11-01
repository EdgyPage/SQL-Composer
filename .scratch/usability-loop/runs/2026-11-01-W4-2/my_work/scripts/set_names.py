"""Fill in one code cell of a notebook: the cell whose first line starts with a given text."""
import json
import sys
from pathlib import Path

path, starts_with, new_source_file = sys.argv[1], sys.argv[2], sys.argv[3]
notebook = json.loads(Path(path).read_text(encoding="utf-8"))
new_source = Path(new_source_file).read_text(encoding="utf-8")
lines = new_source.splitlines(keepends=True)
hits = [c for c in notebook["cells"] if c["cell_type"] == "code" and "".join(c["source"]).startswith(starts_with)]
assert len(hits) == 1, f"found {len(hits)} cells"
hits[0]["source"] = lines
Path(path).write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("saved", path)
