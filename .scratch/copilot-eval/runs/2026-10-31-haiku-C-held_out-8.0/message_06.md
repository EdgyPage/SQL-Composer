You are standing in for Microsoft Copilot in a web chat. Use no tools: answer from what is written here and what you already know.

Before asking anything, the user pasted this as their first message:

<<<
# Copilot file 06: saving a table (sqlglot Composer 8.0)

Objective: write a Saved table from a Statement, in its Table notebook.
Load this file when the user wants to save rows into a table of their own, write a day of
it, add to it, or write the logic cell of a Table notebook.

You write Python for sqlglot Composer 8.0, a Toolbox that writes Hive. Answer with one Python code
block the user can paste into a notebook cell, then a few plain sentences.

## Always

1. Import each name you use, by name: `from sqlglot_composer import FROM, SELECT, statement`.
   Never `import *`. Use only the Toolbox names this file shows; never make one up. Hive's
   own words are Toolbox names only where this file writes them as functions, as SELECT and
   FROM: there is no COUNT, SUM, AND, CASE or ALIAS.
2. Build a Statement with `statement(...)`, its Clause functions in SQL order: a write's
   INSERT_OVERWRITE or INSERT_INTO first, then SELECT or SELECT_DISTINCT, FROM, the joins,
   WHERE, GROUP_BY, HAVING, ORDER_BY, LIMIT.
3. Name every calculation with AS: `AS(count_rows(), "runs")`. A plain column needs none.
   Arithmetic, `+ - * /`, works on Columns; comparisons don't (rule 4).
4. Write each Condition with a function: equals, not_equals, more_than, less_than,
   at_least, at_most, between, is_in, is_not_in, is_null, is_not_null, all_of, any_of. Never
   Python's ==, <, >, and, or, not on a Column. WHERE(a, b) keeps rows where both hold.
5. Bound every read of a partitioned table with a Condition giving a value for one of its
   partition columns, such as `equals(t.dt, "2026-09-24")`, `between(...)`, `is_in(...)` or
   `last_n_days(t.dt, 7)`: in WHERE for FROM, JOIN and CROSS_JOIN; inside ON= for LEFT_JOIN,
   SEMI_JOIN and ANTI_JOIN; for FULL_JOIN, in a Derived table it reads. Matching it to another
   table's column bounds nothing. A table with no partitions needs no bound.
6. ORDER_BY needs LIMIT.
7. Run a read with `run_query(s, query)` and a write with `run_execute(s, execute)`, after
   `from warehouse import query, execute`. Never call query or execute yourself.
8. Add an opt-out, such as `reads_all_partitions=True`, only when the user asks for what it
   allows, and say why in a comment.
9. Reach a column as `table.column`, from the user's Table reference:
   `from references.ops__job_runs import job_runs`, then `job_runs.dt`.
10. The user loads one Copilot file per chat, or for an Excel workbook 11 and 12 with 03,
    04 and 05. When this one doesn't cover what is asked, say so and name the file that
    does, to load in a new chat: 01 imports and the Project, 02 Table references, 03
    building a Statement, 04 joins, 05 windows and subtotals, 06 saving a table, 07
    converting Hive, 08 checking and comparing, 09 fixing a refusal, 10 labels, Hive
    functions and Hive written by hand, 11 and 12 an Excel workbook into Hive.

## Names for this objective, with their arguments

- project.new_table(name, template='saved_table')
- project.load(name)
- project.run_tables(*, execute=None, tables=None)
- create_table(t, may_exist=False)
- INSERT_OVERWRITE(table, unproven_key=False, partition=None)
- INSERT_INTO(table, unproven_key=False, partition=None)
- hive_settings(*names, sets=None)
- statement(*clauses, returns_all_rows=False)
- SELECT_DISTINCT(*columns)
- AS(expression, name)
- count_rows(where=None, over=None)
- run_query(s, query=None)
- run_execute(s, execute=None)
- show_hive(*statements)

## Steps

1. In the new_table Workflow, admin/workflows/new_table/new_table.ipynb (file 13),
   `project.new_table("mart.job_day_events")` makes the Table notebook,
   tables/mart__job_day_events/mart__job_day_events.ipynb, and the Table reference,
   references/mart__job_day_events.py. The user fills in the reference's columns and its
   `<LOCATION>` (file 02).
2. The notebook's logic cell starts with the line `# logic` and holds only imports,
   constants and functions; nothing in it runs Hive. Keep the shape the notebook already has:
   - `READS`, the Condition that picks the rows it reads, such as a day;
   - `create()` returns `create_table(job_day_events, may_exist=True)`;
   - `rows()` returns the list of Clauses that give the rows: SELECT, FROM, `WHERE(READS)`,
     GROUP_BY;
   - `preview()` returns `statement(*rows())`, to read before writing;
   - `write()` returns `statement(INSERT_OVERWRITE(job_day_events), *rows())`.
   `Clause` and `Statement` are the names the hints use.
3. The write's SELECT gives exactly the Saved table's columns, by name, in its order, the
   partition column last. Name a calculation after its column: `AS(count_rows(), "events")`.
4. INSERT_OVERWRITE replaces each Partition the rows hold; INSERT_INTO adds the rows to
   what is there. `INSERT_OVERWRITE(t, partition={"dt": day})` writes one named Partition,
   its column left out of SELECT.
5. A Saved table with a Key takes rows one per Key: GROUP_BY over the Key, SELECT_DISTINCT,
   or a row_number kept at 1 (file 05). Otherwise the write is refused.
6. The notebook's next cell looks: `show_hive([create(), write()])` shows the Hive, any
   Session setting a write needs first included, and `run_query(preview(), query)` reads
   the rows. The writes are sent by `project.run_tables(execute=execute)`, in
   admin/run_tables.ipynb: each Saved table after the tables it reads, its Session settings
   first.
7. To send one table by hand: `run_execute(create(), execute)` once, then
   `run_execute(hive_settings("dynamic_partitions"), execute)`, as a write whose rows fill
   their Partitions needs, then `run_execute(write(), execute)`.
8. From another notebook, `project.load("mart.job_day_events")` gives that cell's functions,
   such as its `write()`.

## Worked example

The logic cell of mart.job_day_events, each job's events of a day:

```python
# logic
from sqlglot_composer import (AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, Clause,
                              Statement, count_rows, create_table, equals, statement)
from references.mart__job_day_events import job_day_events
from references.ops__job_events import job_events

READS = equals(job_events.dt, "2026-09-24")


def create() -> Statement:
    return create_table(job_day_events, may_exist=True)


def rows() -> list[Clause]:
    return [
        SELECT(job_events.job_id, AS(count_rows(), "events"), job_events.dt),
        FROM(job_events),
        WHERE(READS),
        GROUP_BY(job_events.job_id, job_events.dt),
    ]


def preview() -> Statement:
    return statement(*rows())


def write() -> Statement:
    return statement(INSERT_OVERWRITE(job_day_events), *rows())
```

Its Table reference, references/mart__job_day_events.py, lists job_id bigint, events bigint and
dt string, partitioned by dt, with Key job_id and dt, and a location (file 02).

## Do and don't

- Do put the write clause first: `statement(INSERT_OVERWRITE(t), SELECT(...), ...)`.
- Do select every column of the Saved table, named as it names them, partition last.
- Don't call run_query or run_execute in the logic cell: `project.load` refuses it.
- Don't use INSERT_INTO where the user wants a day replaced; it adds rows twice on a rerun.
- Don't pass `unproven_key=True` unless the user says the rows are one per Key for a reason
  the Toolbox can't see.

## Before you answer

- The logic cell starts with `# logic` and only imports, sets constants and defines.
- The write's columns match the Saved table's, with the Key proved by GROUP_BY or the like.
- Every partitioned table read is bounded; the write sends with run_execute.

>>>

Each task below is a separate request the user sends next. Answer each as you would in that chat: reply with its `## T..` heading, then your answer, with the code in a ```python block.

## T18

I work in a sqlglot Composer 8.0 Project. Its references:
- `from references.ops__job_runs import job_runs` gives ops.job_runs: run_id bigint, job_id bigint, status string, duration_mins int, avg_retry_secs double, dt string; partitioned by dt; Key run_id.
- `from references import ops` gives each ops table above by its name, as ops.job_runs.
- references/mart__job_day_runs.py holds:

from sqlglot_composer import Table

job_day_runs = Table(
    "mart.job_day_runs",
    columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    partitioned_by=["dt"],
    key=["job_id", "dt"],
    location="/data/your_team/mart.db/job_day_runs",
)

- `from warehouse import query, execute` gives my two calls to the warehouse.

Add each job's number of runs in ops.job_runs on 2026-09-23 to my Saved table mart.job_day_runs (from references.mart__job_day_runs import job_day_runs), keeping what it already holds.

Answer with one Python code block that builds it and assigns the Statement to `s`.
