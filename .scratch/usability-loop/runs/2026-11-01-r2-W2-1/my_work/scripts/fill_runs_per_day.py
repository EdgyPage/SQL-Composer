"""Fill in the placeholders of the mart_dev.runs_per_day Table notebook, by hand, as its markdown says."""
import json
from pathlib import Path

NB = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-W2-1\my_work\tables\mart_dev__runs_per_day\mart_dev__runs_per_day.ipynb")
nb = json.loads(NB.read_text(encoding="utf-8"))

REPLACEMENTS = [
    ("from references.<SOURCE_NAME> import <SOURCE_TABLE>", "from references.ops__job_runs import job_runs"),
    ("    AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, Clause, Statement, count_rows,\n",
     "    AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, Clause, Statement, between, count_rows,\n"),
    ("READS = <READS>", 'READS = between(job_runs.dt, "2026-09-23", "2026-09-24")'),
    ('PARTITIONED_BY = ["<PARTITION_COLUMN>"]', 'PARTITIONED_BY = ["dt"]'),
    ("<SOURCE_TABLE>", "job_runs"),
    ("<GROUP_COLUMN>", "job_id"),
    ("<COUNT_NAME>", '"runs"'),
    ("<PARTITION_COLUMN>", "dt"),
]

logic = nb["cells"][2]
text = "".join(logic["source"])
assert text.startswith("# logic"), text[:40]
for old, new in REPLACEMENTS:
    assert old in text, old
    text = text.replace(old, new)
logic["source"] = text.splitlines(keepends=True)

md = nb["cells"][0]
mtext = "".join(md["source"])
old = "TODO: say in one line what one row of mart_dev.runs_per_day is."
assert old in mtext
mtext = mtext.replace(old, "One row is one job's runs on one day of ops.job_runs: its job_id, its runs, and its dt.")
md["source"] = mtext.splitlines(keepends=True)

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("filled")
