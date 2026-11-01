"""Fill in the names cell and the step 1 decision of change_a_saved_table, as its notebook asks."""
from pathlib import Path

nb = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-W5-1\my_project\admin\workflows\change_a_saved_table\change_a_saved_table.ipynb")
text = nb.read_text(encoding="utf-8")
pairs = [
    ("TABLE = ''  # the Saved table to change", "TABLE = 'mart_dev.runs_per_day'  # the Saved table to change"),
    ("change = admin.drop_partitions(table, where=...)", "change = admin.drop_partitions(table, where=equals(table.dt, '2026-09-24'))"),
]
for old, new in pairs:
    assert text.count(old) == 1, (old, text.count(old))
    text = text.replace(old, new)
nb.write_text(text, encoding="utf-8")
print("written")
