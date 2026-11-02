"""Replace one exact string, which must occur once, in a notebook's raw JSON text.
Usage: replace_in_notebook.py NOTEBOOK OLD_FILE NEW_FILE"""
import sys
from pathlib import Path

notebook, old, new = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
text = notebook.read_text(encoding="utf-8")
old_text, new_text = old.read_text(encoding="utf-8"), new.read_text(encoding="utf-8")
count = text.count(old_text)
if count != 1:
    sys.exit(f"Found {count} matches, expected 1: nothing changed")
notebook.write_text(text.replace(old_text, new_text), encoding="utf-8")
print("Replaced one line in", notebook.name)
