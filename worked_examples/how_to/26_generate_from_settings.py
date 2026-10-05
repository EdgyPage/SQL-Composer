"""Generate Table references and Statements from settings

For: Intermediate

## Goal

Write down what you know about each table once, as settings: its name, its key and the columns
worth adding up. From those settings, generate a Table reference and a daily Statement for
every table, run them all, and export one Lineage for the lot.

## When you'd use it

When the same job repeats over many tables: daily totals for every table a team owns, or one
check per table. Adding a table is then one more line of settings, not one more copied
Statement, and a fix to the function that writes the Statements reaches every table at once.
[Generate Statements in a loop](#generate_statements_in_a_loop) starts with a loop over one
table; this how-to loops over tables.

## Steps

### Import the Toolbox

>>> from sqlglot_composer import *
>>> import datetime

### Write one setting per table

Each setting is a dict: the table's name, its key, and under `"add_up"` the columns a daily
total adds up. `ops.job_events` has no column worth adding up, so its `"add_up"` is an empty
list and its total is the number of rows. `ops.region_costs` writes its days like 20260924,
which its setting says in `"date_format"`, as a Table reference does. The avg_retry_secs column
of `ops.job_runs` is an average, which must never be added up, so its setting lists it in
`"does_not_add_up"`.

>>> settings = [
...     {"table": "ops.job_runs", "key": ["run_id"], "add_up": ["duration_mins"],
...      "does_not_add_up": ["avg_retry_secs"]},
...     {"table": "ops.job_events", "key": ["event_id"], "add_up": []},
...     {"table": "ops.region_costs", "key": ["job_id", "region", "dt"],
...      "add_up": ["cost_cents"], "date_format": "%Y%m%d"},
... ]

### Generate a Table reference for each table

A Table reference needs each column and its type. Rather than type them, ask the table, as
[Import a table's column names](#import_column_names) does: your send runs DESCRIBE, which lists
the columns, one per row, each with its name in `"col_name"` and its type in `"data_type"`.
After them it lists the partition columns again, under a heading row starting with `#`, often
after an empty row, so stop at the first such row:

>>> example_database.send("DESCRIBE ops.region_costs")
                  col_name  data_type                       comment
0                   job_id     bigint
1               cost_cents     bigint  NULL until the bill comes in
2                   region     string
3                       dt     string
4                                None                          None
5  # Partition Information       None                          None
6               # col_name  data_type                       comment
7                   region     string
8                       dt     string

`table_reference` builds a Table reference from a setting and what DESCRIBE gives. Every
table here keeps its days in a column named dt; if yours don't, add the name to each setting
too:

>>> def table_reference(setting, send):
...     described = send("DESCRIBE " + setting["table"])
...     columns = {}
...     for name, data_type in zip(described["col_name"], described["data_type"]):
...         if not name or name.startswith("#"):
...             break
...         columns[name] = data_type
...     return Table(setting["table"], columns=columns, date_partition="dt",
...                  key=setting["key"], does_not_add_up=setting.get("does_not_add_up", []),
...                  date_format=setting.get("date_format"))
>>> tables = {setting["table"]: table_reference(setting, example_database.send)
...           for setting in settings}
>>> tables["ops.region_costs"]
Table('ops.region_costs', columns: job_id, cost_cents, region, dt)

Check what you generated, as you would a Table reference you wrote: each still matches its
table, and each key holds.

>>> for t in tables.values():
...     print(check_table_reference(t, send=example_database.send))
...     print(check_key(t, send=example_database.send))
ops.job_runs matches its Table reference.
ops.job_runs: the key (run_id) holds on 2026-09-24.
ops.job_events matches its Table reference.
ops.job_events: the key (event_id) holds on 2026-09-24.
ops.region_costs matches its Table reference.
Notes:
  - the table is also partitioned by region, which a Statement may bound too.
ops.region_costs: the key (job_id, region, dt) holds on 20260924.

A Table reference generated like this lasts as long as the notebook. For a table you build on
for months, write its Table reference to a file once with
[`write_table_reference`](examples.html#write_table_reference) and keep it, so a change to the
table shows up as a difference when you check it, rather than slipping into your Statements.

### Generate a Statement for each table

`daily_totals` writes one Statement for a table and its setting: per day, the number of rows and
the total of each column it adds up. `getattr(t, "duration_mins")` is `t.duration_mins`, for a
column whose name you hold as text, so a column the table doesn't have stops here, naming the
real ones.

>>> def daily_totals(t, setting, first_day, last_day):
...     totals = [AS(sum_of(getattr(t, name)), "total_" + name)
...               for name in setting["add_up"]]
...     return statement(
...         SELECT(t.dt, AS(count_rows(), "row_count"), totals),
...         FROM(t),
...         WHERE(between(t.dt, first_day, last_day)),
...         GROUP_BY(t.dt),
...     )

The days are given as `datetime.date`, not as text: each table writes them in its own way, and
`between` writes a `datetime.date` as the table's Table reference says. Generate one
Statement per setting, and see their Hive:

>>> first_day, last_day = datetime.date(2026, 9, 23), datetime.date(2026, 9, 24)
>>> daily = {setting["table"]: daily_totals(tables[setting["table"]], setting,
...                                           first_day, last_day)
...          for setting in settings}
>>> text = show_hive(*daily.values())
-- 1 of 3
SELECT
  job_runs.dt,
  COUNT(*) AS row_count,
  SUM(job_runs.duration_mins) AS total_duration_mins
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
GROUP BY
  job_runs.dt;
<BLANKLINE>
-- 2 of 3
SELECT
  job_events.dt,
  COUNT(*) AS row_count
FROM ops.job_events AS job_events
WHERE
  job_events.dt BETWEEN '2026-09-23' AND '2026-09-24'
GROUP BY
  job_events.dt;
<BLANKLINE>
-- 3 of 3
SELECT
  region_costs.dt,
  COUNT(*) AS row_count,
  SUM(region_costs.cost_cents) AS total_cost_cents
FROM ops.region_costs AS region_costs
WHERE
  region_costs.dt BETWEEN '20260923' AND '20260924'
GROUP BY
  region_costs.dt;

### Run them all

Run each in a loop, and keep each result under its table's name:

>>> results = {name: run(totals, send=example_database.send)
...            for name, totals in daily.items()}
>>> results["ops.region_costs"]
         dt  row_count  total_cost_cents
0  20260923          2               300
1  20260924          2               100

On 2026-09-24 `ops.region_costs` has two rows, but only one was billed: invoice_sync's bill
hasn't come in, so its cost is NULL, and SUM leaves a NULL out of the total.

### Export one Lineage for them all

Pass every Statement to [`export_lineage`](examples.html#export_lineage) at once, and it writes
one HTML page and one Markdown file for them all, laid out as in [Lineage of one
Statement](#lineage_of_one_statement). `to=` names the HTML file, and the Markdown file goes
beside it.

`export_lineage` names each Statement after the variable that holds it. These sit in a dict, in
no variable of their own, so it numbers them in the order you passed them: in the file below,
statement_1 is `ops.job_runs`'s, statement_2 `ops.job_events`'s and statement_3
`ops.region_costs`'s, and each one's Hive, at the end of its part, names its table.

>>> html_file, markdown_file = export_lineage(*daily.values(), to="daily_totals.html")

## Check it worked

There is one Table reference, one Statement and one result per setting, and each Table
reference matched its table:

>>> len(settings), len(tables), len(daily), len(results)
(3, 3, 3, 3)
>>> markdown_file.name
'daily_totals.md'

## Common mistakes

### A column to add up that isn't one of the table's

A typo in a setting stops when its Statement is generated, at `getattr`, with the real columns:

>>> typo = {"table": "ops.job_runs", "key": ["run_id"], "add_up": ["duration_min"]}
>>> daily_totals(tables["ops.job_runs"], typo, first_day, last_day)
Traceback (most recent call last):
...
AttributeError: job_runs has no column 'duration_min'. Did you mean 'duration_mins'? Its columns are: run_id, job_id, status, duration_mins, avg_retry_secs, dt.

### Adding up an average

A setting can list under `"add_up"` a column that must not be added up, such as
"avg_retry_secs", an average per run. Because the Table reference was generated with
`"does_not_add_up"` from the setting, the Toolbox refuses it:

>>> averages = {"table": "ops.job_runs", "key": ["run_id"], "add_up": ["avg_retry_secs"]}
>>> daily_totals(tables["ops.job_runs"], averages, first_day, last_day)
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  sum_of(job_runs.avg_retry_secs) adds up job_runs.avg_retry_secs, which is listed in does_not_add_up in its Table reference.
...

Leave a setting's `"does_not_add_up"` out and nothing would refuse it: the total would come out,
and be wrong. Fill it in for every table.

### The same days, written as text, for every table

Text days are written one way, and `ops.region_costs` writes its days another, so the Toolbox
refuses them rather than read no day, or the wrong ones:

>>> daily_totals(tables["ops.region_costs"], settings[2], "2026-09-23", "2026-09-24")
Traceback (most recent call last):
...
ValueError:
  What happened:  between(region_costs.dt, ...) compares the Date partition region_costs.dt with '2026-09-23', which isn't a day written like '20260925'.
...

Pass `datetime.date` days, as the steps do, and each table gets them in its own way. Text
written the table's own way, `"20260923"`, works too, as in [Check data quality with
Statements](#check_data_quality), but then each table needs its days written its own way.

## Next

- [Check data quality with Statements](#check_data_quality): checks you could generate per
  table the same way, from the same settings.
- [Review a change with Lineage](#review_a_change_with_lineage): compare a Lineage before and
  after you change the function that writes your Statements.
- The gallery's [`Table`](examples.html#Table) says what each part of a Table reference does,
  and [`check_table_reference`](examples.html#check_table_reference) what it compares.
"""
