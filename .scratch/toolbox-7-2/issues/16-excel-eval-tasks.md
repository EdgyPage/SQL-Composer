# The Excel evaluation: about 40 workbook tasks, a Hive scorer, and the baseline

Type: task
Status: open
Blocked by: 15
Size: L

## Question

The user (2026-10-28): "yes, test extensively", "be sure the evaulations cover combinations of
cases as well", and a pass rate of "95%+". With 8 held-out tasks one miss is 87.5%, so the user
chose 20 held-out tasks, 95% on Haiku and Sonnet alike.

As with ticket 12, the tasks and the baseline come before file 11 (ticket 17), so the held-out
tasks are written before any file is.

## Done when

- About 40 tasks, 20 dev and 20 held-out, each a workbook built by ticket 15's tool over the
  Example database's tables, with a reference Hive per final Table. Each case below has a task
  of its own, and a combinations tier mixes them (such as a lookup feeding a `SUMIFS`, with a
  typed-over cell and a blank-as-zero mark in one Table), in both splits:
  - each family on the "converts" list: arithmetic, `IF`/`IFS`/`IFERROR`/`SWITCH`,
    `AND`/`OR`/`NOT`, `ROUND` and the math functions, text, dates, `XLOOKUP`/`VLOOKUP`/
    `INDEX`+`MATCH` against another Table, `SUMIFS`/`COUNTIFS`/`AVERAGEIFS`/`MAXIFS`;
  - both reference forms, `[@units]` and `sales[[#This Row],[units]]`;
  - each "converts with a mark" case: a blank counted as 0, `VLOOKUP`'s approximate match,
    dates held as text, a defined name pointing outside a Table;
  - each refused one: `INDIRECT`, `OFFSET`, a reference outside a Table, `LAMBDA`/`LET` across
    sheets, `RAND`, a circular reference;
  - typed-over cells, with a `Keys` Table, and without one (the marked fallback);
  - direction: a chain of steps, a query reading another query, a connection-only query,
    several final Tables from shared sources, raw columns nothing uses, a PivotTable or chart
    to be ignored;
  - Table names and headers that aren't the Hive names (`Sales Data`, `Unit Price`, `% Margin`);
  - Power Query M, given as text in the task, since the tool writes no M: each step on the M
    "converts" list, a marked source (`Sql.Database`), a refused one (`Web.Contents`).
- The proxies get each workbook as text: each Table's name, headers, sample rows and formulas,
  and each query's M, written by the tool from the .xlsx (and the task's M).
- `tools/copilot_eval.py` scores an Excel answer:
  - the map is there, naming the sources, steps and finals;
  - each Hive query, its `<...>` filled with the task's names, runs on the Example database and
    gives the reference's rows;
  - every typed-over cell is reproduced;
  - every refused function is named, never guessed;
  - no Table or column name is invented without `<...>`;
  - the Toolbox draft is scored by the existing Python scorer, as a secondary score that doesn't
    decide the pass.
- `tests/test_copilot_eval.py`: every reference scores a pass, and a negative control fails on
  each check: a dropped typed-over cell, a guessed `INDIRECT`, an unbracketed invented name, a
  missing map, wrong rows.
- The A0 baseline on dev, on Haiku, in `.scratch/copilot-eval/results.md`.
