import json, pathlib
nb = pathlib.Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-W5-3\my_project\admin\workflows\change_a_saved_table\change_a_saved_table.ipynb")
text = nb.read_text(encoding="utf-8")
BS = chr(92)  # a backslash, as the notebook's JSON writes an escaped quote
Q = chr(34)   # a double quote
edits = [
    (Q + "from sqlglot_composer import admin, hive_settings, project, run_execute, run_query, show_hive" + BS + "n" + Q + ",",
     Q + "from sqlglot_composer import admin, equals, hive_settings, project, run_execute, run_query, show_hive" + BS + "n" + Q + ","),
    ("TABLE = '')  # the Saved table to change" if False else "TABLE = ''  # the Saved table to change, such as " + BS + Q + "mart.daily_job_runs" + BS + Q,
     "TABLE = " + BS + Q + "mart_dev.runs_per_day" + BS + Q + "  # the Saved table to change, such as " + BS + Q + "mart.daily_job_runs" + BS + Q),
    ("change = admin.drop_partitions(table, where=...)  # or another: help(admin)",
     "change = admin.drop_partitions(table, where=equals(table.dt, " + BS + Q + "2026-09-24" + BS + Q + "))  # or another: help(admin)"),
]
for old, new in edits:
    n = text.count(old)
    assert n == 1, (n, old)
    text = text.replace(old, new)
nb.write_text(text, encoding="utf-8")
cells = json.loads(text)["cells"]
for c in cells:
    if c["cell_type"] == "code":
        print("".join(c["source"]))
        print("-----")
