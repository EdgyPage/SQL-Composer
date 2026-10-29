# The Excel evaluation: about 40 workbook tasks, a Hive scorer, and the baseline

Type: task
Status: resolved
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

## Answer

Built 2026-10-29. `tools/excel_eval_tasks.py` describes 40 filled-in Formula workbooks, X01 to
X40, 20 dev and 20 held out; every kind in `COVERAGE` (49: each formula family, both
reference forms, each mark, each refusal, typed-over values with and without Keys, each
direction case, renamed Tables and headers, each Power Query step) has a task in each split,
and `combination` tasks mix several, X09 and X14 on dev, X38 to X40 held out.
`tools/formula_workbook.py` builds each (`build`) and writes what Copilot reads in it
(`as_text`), read back from the saved file: formulas as the file holds them
(`job_runs[[#This Row],[x]]`, `_xlfn.XLOOKUP`), or as typed where a task says so.
`tools/excel_eval.py` prints the prompts, the proxy message and an answers template, writes
the workbooks for the manual round, and scores.

**The A0 baseline on dev, on Haiku: 0% passed**, 100% found and parsed, 90% ran, 75%
correct, 0% mapped, 70% named everything, 5% invented a name. Without file 11, Haiku already
gets most rows right; it never says which Tables are the sources and the finals, and misses
the refusals, the blank cell and the Keys.

Settled while building:

- **The stand-in Hive is SQLite**, holding the Example database's rows in `ops`, each query
  turned from Hive by sqlglot, with Hive's MONTH, YEAR, DAY and PMOD added. The Example
  database's executor has no date functions on a column (sqlglot wraps them in TO_DATE), no
  PMOD and no CAST. A test holds SQLite to the executor's own rows on every reference it can
  run: 42 of 44 finals, all but X05's and X24's dates.
- **Its own command line**, `tools/excel_eval.py`, not `copilot_eval.py`'s: the checks, the
  score and the results columns differ. It reuses `invented_names` for the draft.
- **A refused formula is NULL in the reference**, its column kept: file 11 has Copilot leave
  its place empty, as the Steps sheet says.
- **Sources are read from typed columns**, refining the map's "a Table that reads no other
  Table": a Table's typed columns stand for its database table, so a Table with data and
  formulas reading another Table (X06's job_runs) is a source and a final at once; a Table
  whose only typed columns are what its SUMIFS matches on is a summary, a GROUP BY.
- **What is invented**: a table, database or column the reply writes without `<...>` that the
  workbook doesn't give (its Tables, headers, queries, the names its M quotes or brackets,
  defined names, Parameters) and the query doesn't define. A `<database>` the person fills in
  is told apart from a database the reply wrote itself, so a bare `ops.job_runs` is a guess
  unless the workbook names `ops` (X19's `Sql.Database(..., "ops")`).
- **The draft decides nothing**: it is scored on whether it parses once its `<...>` are filled
  and on the Toolbox names it invents, not run, since `convert` writes the checked code from
  the Hive.
- **Not built**: a task with LET (it converts row by row; only a LAMBDA is refused); a check
  of the steps in the map (only sources and finals are named); a separate typed-over check
  (the rows hold it).

Reviews, on 7f649da:

- **Standards**: fixed the bare `tuple` hints, `runs_table`/`jobs_table` taking their
  arguments by name, CASES renamed COVERAGE (the glossary avoids "case"), the reason for
  `_add_table`'s local import, `names_sources_and_finals`. Kept `excel_eval.py`'s repetition
  of `copilot_eval.py`'s shapes, which standards.md prefers to a shared helper with flags.
- **Spec**: fixed the guessed `ops`, the substring test for known names (now the workbook's
  own names), names matched only in the reply's words outside its code (the text date's mark
  is now "as text"), the map naming each source; the pivots' and X33's references now NULL
  as M leaves it. The docs say to add a task's PivotTable by hand for the manual round.
- **Drift**: clean.
