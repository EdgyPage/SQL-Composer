"""Replace one source line of a notebook's code cell, in the file's own text.

usage: nb_line.py NOTEBOOK OLD_LINE NEW_LINE   (lines given without their newline)
The lines are matched as they sit in the notebook's JSON source lists, so quotes and
backslashes are escaped for you. A cell's last line has no newline in the JSON; the
others end with an escaped newline, which is tried first.
"""
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
old, new = sys.argv[2], sys.argv[3]
text = path.read_bytes().decode("utf-8")


def as_json_text(line: str) -> str:
    return json.dumps(line, ensure_ascii=False)[1:-1]


for ending in ("\n", ""):
    old_e = as_json_text(old) + ending
    new_e = as_json_text(new) + ending
    if text.count(old_e) == 1:
        break
else:
    sys.exit("expected one match, found none or several")
path.write_bytes(text.replace(old_e, new_e).encode("utf-8"))
json.loads(path.read_text(encoding="utf-8"))  # still valid JSON
print("replaced")
