"""Fill in the <...> placeholders of the runs_per_day Table notebook, and its one TODO line."""
import json

NB = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r20-W2-3\my_work\tables\mart_dev__runs_per_day\mart_dev__runs_per_day.ipynb"

CODE_REPLACEMENTS = [
    ("from references.<SOURCE_NAME> import <SOURCE_TABLE>",
     "from references.ops__job_runs import job_runs", 1),
    ("# each table it reads, such as: from references.ops__job_runs import job_runs\n", "", 1),
    ("    AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, Clause, Statement, count_rows,\n    create_table, equals, statement,\n",
     "    AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, Clause, Statement, between,\n    count_rows, create_table, statement,\n", 1),
    ("READS = <READS>", 'READS = between(job_runs.dt, "2026-09-23", "2026-09-24")', 1),
    ('PARTITIONED_BY = ["<PARTITION_COLUMN>"]', 'PARTITIONED_BY = ["dt"]', 1),
    ("<SOURCE_TABLE>.<GROUP_COLUMN>", "job_runs.job_id", 2),
    ("<COUNT_NAME>", '"runs"', 1),
    ("<SOURCE_TABLE>.<PARTITION_COLUMN>", "job_runs.dt", 2),
    ("FROM(<SOURCE_TABLE>)", "FROM(job_runs)", 1),
]
TEXT_REPLACEMENTS = [
    ("TODO: say in one line what one row of mart_dev.runs_per_day is.",
     "One row is one job's runs on one day: its job_id and dt, with the count of its runs (runs).", 1),
]

with open(NB, encoding="utf-8") as f:
    nb = json.load(f)


def edit(text: str, replacements) -> str:
    for old, new, count in replacements:
        found = text.count(old)
        if found:
            assert found == count, (old, found)
            text = text.replace(old, new)
    return text


changed = []
for i, cell in enumerate(nb["cells"]):
    source = "".join(cell["source"])
    if cell["cell_type"] == "code":
        new = edit(source, CODE_REPLACEMENTS)
    else:
        new = edit(source, TEXT_REPLACEMENTS)
    if new != source:
        cell["source"] = new.splitlines(keepends=True)
        changed.append((i, cell["cell_type"]))

with open(NB, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")
print("changed cells (index, type):", changed)
