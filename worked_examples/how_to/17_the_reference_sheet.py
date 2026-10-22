"""The Reference sheet

For: Getting started

## Goal

See every column of every table your Project reads or writes in one table: its type, whether
it is a partition column or in the Key, its Aliases and what it holds.
`project.refresh_reference_sheet()` writes it, references/reference_sheet.csv, from the Table
references in references/, to read in pandas, a spreadsheet, or any program that opens a CSV
file.

## When you'd use it

When you look for a column and don't know which table has it, when someone new asks what the
Project's tables hold, and after you fill in or change a Table reference. The sheet is read
from the Table references, never from the warehouse, so it says what your files say: refresh
it whenever you change one.

## Steps

### Start a Project with three tables' references

These steps run in a Project, as [Start a Project](#start_a_project) makes one, with the Table
references [Add your tables' references](#add_your_tables_references) writes. In your own Project, which is started already, leave out `project.start()`: it refuses a
folder that is a Project. This page has none, so it starts one,
writes three, and gives `ops.job_runs` two Aliases, as you would in your editor:

>>> from pathlib import Path
>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/ and warehouse.py. Next: write your query and execute in warehouse.py.
>>> project.add_references(["ops.jobs", "ops.job_runs", "ops.run_alerts"],
...                        query=example_database.query)
Wrote references/ops__jobs.py, references/ops__job_runs.py and references/ops__run_alerts.py: fill in their TODO lines.
Wrote references/ops.py: from references import ops gives ops.job_runs, ops.jobs and ops.run_alerts.
Restart the kernel of a notebook that imported references, to see a table added since.
>>> reference = Path("references/ops__job_runs.py")
>>> text = reference.read_text(encoding="utf-8").replace(
...     "from sqlglot_composer import Table", "from sqlglot_composer import Table, equals")
>>> text += 'minutes = job_runs.duration_mins\\nfailed = equals(job_runs.status, "FAILED")\\n'
>>> size = reference.write_text(text, encoding="utf-8")

### Write the sheet

>>> project.refresh_reference_sheet()
Wrote references/reference_sheet.csv: 14 rows, 3 tables.

It has a row per column of each table, and these columns:

- table and column: the table's name, such as ops.job_runs, and the column's;
- type: its Hive type, such as bigint;
- partition and in_key: "yes" for each of the table's partition columns, and for each column
  of its Key, as its Table reference's `partitioned_by=` and `key=` say;
- aliases: each Alias written below the Table reference that reads this column alone, a
  condition shown as "failed (a condition)";
- description: what the column holds, from the Table reference's `descriptions=`;
- exported_at: when the sheet was written.

### Read it in pandas

Python's own `csv` module reads it, and pandas makes a DataFrame of it. `csv` keeps an empty
cell as empty text, `""`, so a test such as `sheet.aliases != ""` picks the filled ones.
Open it in a spreadsheet program just as well: it is plain CSV.

>>> import csv
>>> import pandas as pd
>>> with open("references/reference_sheet.csv", encoding="utf-8", newline="") as file:
...     sheet = pd.DataFrame(csv.DictReader(file))

Every table that has a column named job_id, to see where a join on it could go:

>>> sheet[sheet.column == "job_id"][["table", "type", "in_key"]]
           table    type in_key
1   ops.job_runs  bigint
6       ops.jobs  bigint

Neither says "yes" under in_key yet: their Table references still say `key=None`, a TODO left
to fill in. The sheet shows what the files say, so it shows what is missing too.

Every Alias, and the column it reads:

>>> sheet[sheet.aliases != ""][["table", "column", "aliases"]]
          table         column               aliases
2  ops.job_runs         status  failed (a condition)
3  ops.job_runs  duration_mins               minutes

### Refresh one table's rows

After you change one Table reference, refresh its rows alone: the others keep theirs, and
their exported_at, as they were.

>>> project.refresh_reference_sheet("ops.job_runs")
Wrote references/reference_sheet.csv: 14 rows, 3 tables.

A Table notebook's last cell does this for its own table, as
[Add a Saved table](#add_a_saved_table) shows, and the admin notebook
admin/refresh_reference_sheet.ipynb rebuilds the whole sheet.

## Check it worked

The sheet has a row for each column of the three tables, and the Aliases written by hand:

>>> sorted(set(sheet.table))
['ops.job_runs', 'ops.jobs', 'ops.run_alerts']
>>> len(sheet)
14
>>> sorted(sheet.aliases[sheet.aliases != ""])
['failed (a condition)', 'minutes']

## Common mistakes

### A Table reference still to fill in

A Saved table's Table reference, as `project.new_table` writes it, holds `<...>` to fill in, so
it isn't Python yet and the sheet can't read it. The sheet leaves it out, and says so:

>>> project.new_table("mart.daily_job_runs")
Made tables/mart__daily_job_runs/: mart__daily_job_runs.ipynb and lineage/, from
admin/templates/saved_table.py.
Wrote references/mart__daily_job_runs.py: fill in its <...> and TODO lines.
>>> project.refresh_reference_sheet()
Wrote references/reference_sheet.csv: 14 rows, 3 tables.
Left out, since it can't be read yet: references/mart__daily_job_runs.py. Fill in every <...> in it, and check it holds a Table(...) call, then refresh again.

Fill in the file, as [Add a Saved table](#add_a_saved_table) shows, then refresh again.

### Editing the sheet by hand

Each refresh writes the sheet again from the Table references, so a change typed into the CSV
file is gone the next time. Write a description in the Table reference's `descriptions=`, and
an Alias below its Table(...) call, then refresh: the file is where it lives, and the sheet
only shows it.

## Next

- Fill in each Table reference's key and descriptions:
  [Add your tables' references](#add_your_tables_references).
- Keep each Table reference true as its table changes:
  [Keep a Table reference true over time](#keep_a_table_reference_true_over_time).
- Follow a column of a Saved table back to the tables it reads:
  [Lineage across your tables](#lineage_across_your_tables).
- The gallery's [`Table`](examples.html#Table) entry.
"""
