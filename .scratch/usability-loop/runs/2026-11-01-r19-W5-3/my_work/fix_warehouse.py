"""Replace the mangled connection lines of my_project/warehouse.py with the lines the README's step 5 gives.

The file's import sys was commented out inside a comment block, so sys.path was used before it
was imported, and the connection lines were written twice. The README's step 5 gives the lines to
write in place of conn = example_database; this writes them, with the work folder, where
team_connection.py is, as the folder to append to the path.
"""
from pathlib import Path

WH = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r19-W5-3\my_project\warehouse.py")
text = WH.read_bytes().decode("utf-8").replace("\r\n", "\n")
lines = text.split("\n")

start = lines.index("# Your connection to the warehouse. At work, replace example_database with your own, such as")
end = lines.index("from team_connection import conn  # noqa: E402", start + 3) + 1  # the second, last one
# The block to replace: from the comment above conn through the last team_connection import.
block = [
    "# Your connection to the warehouse. At work, replace example_database with your own, such as",
    "# conn = your_library.connect(...): its query(sql) gives back a DataFrame, and its",
    "# execute(sql) runs Hive that changes something. A connection kept in a file outside the",
    "# Project, such as team_connection.py, is imported by these lines, in place of the line",
    "# conn = example_database below:",
    "#     import sys",
    '#     sys.path.append("C:/work/connections")  # the folder team_connection.py is in',
    "#     from team_connection import conn",
    "import sys",
    "",
    'sys.path.append("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r19-W5-3")  # the folder team_connection.py is in',
    "from team_connection import conn",
]
new_lines = lines[:start] + block + lines[end:]
out = "\n".join(new_lines)
WH.write_bytes(out.replace("\n", "\r\n").encode("utf-8"))
print("written")
