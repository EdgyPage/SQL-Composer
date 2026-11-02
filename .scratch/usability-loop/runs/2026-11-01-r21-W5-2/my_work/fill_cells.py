"""Fill two code lines of change_a_saved_table.ipynb, in place, keeping its CRLF line endings.

Each replacement must match exactly one line of the notebook's file.
"""
import sys
from pathlib import Path

NOTEBOOK = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs"
                r"\2026-11-01-r21-W5-2\my_project\admin\workflows\change_a_saved_table"
                r"\change_a_saved_table.ipynb")

REPLACEMENTS = [
    (r"""    "TABLE = ''  # the Saved table to change, such as \"mart.daily_job_runs\"" """.rstrip(),
     r"""    "TABLE = \"mart_dev.runs_per_day\"  # the Saved table to change, such as \"mart.daily_job_runs\"" """.rstrip()),
    (r"""    "change = admin.drop_partitions(table, where=...)  # or another: help(admin)" """.rstrip(),
     r"""    "change = admin.drop_partitions(table, where=equals(table.dt, \"2026-09-24\"))  # or another: help(admin)" """.rstrip()),
]

text = NOTEBOOK.read_bytes().decode("utf-8")
for old, new in REPLACEMENTS:
    old_line = old + "\r\n"
    new_line = new + "\r\n"
    count = text.count(old_line)
    if count != 1:
        sys.exit(f"expected one match, found {count}: {old!r}")
    text = text.replace(old_line, new_line)
NOTEBOOK.write_bytes(text.encode("utf-8"))
print("filled 2 lines")
