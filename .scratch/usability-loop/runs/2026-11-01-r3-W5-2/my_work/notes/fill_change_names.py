"""Fill in the change_a_saved_table names cell and its step 1 where= for mart_dev.runs_per_day."""
import json
import sys

path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    nb = json.load(f)

done = {"names": False, "where": False}
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    text = "".join(cell["source"])
    new = text
    if text.startswith("TABLE = ''"):
        new = text.replace("TABLE = ''", 'TABLE = "mart_dev.runs_per_day"', 1)
        done["names"] = True
    elif "change = admin.drop_partitions(table, where=...)" in text:
        new = text.replace("where=...)", 'where=equals(table.dt, "2026-09-24"))', 1)
        done["where"] = True
    if new != text:
        lines = new.splitlines(keepends=True)
        cell["source"] = lines

assert all(done.values()), done
with open(path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")
print("filled", done)
