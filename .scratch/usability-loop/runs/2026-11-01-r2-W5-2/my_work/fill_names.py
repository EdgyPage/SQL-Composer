import json
import pathlib

p = pathlib.Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-W5-2\my_project\admin\workflows\change_a_saved_table\change_a_saved_table.ipynb")
text = p.read_bytes().decode("utf-8")
old1 = "TABLE = ''  # the Saved table to change"
new1 = 'TABLE = \\"mart_dev.runs_per_day\\"  # the Saved table to change'
old2 = "change = admin.drop_partitions(table, where=...)  # or another: help(admin)"
new2 = 'change = admin.drop_partitions(table, where=equals(table.dt, \\"2026-09-24\\"))  # or another: help(admin)'
assert text.count(old1) == 1 and text.count(old2) == 1
text = text.replace(old1, new1).replace(old2, new2)
nb = json.loads(text)
p.write_bytes(text.encode("utf-8"))
for cell in nb["cells"]:
    if cell["cell_type"] == "code" and ("TABLE" in "".join(cell["source"]) or "drop_partitions" in "".join(cell["source"])):
        print("".join(cell["source"]))
print("ok")
