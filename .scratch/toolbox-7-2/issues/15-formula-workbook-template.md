# The Formula workbook template, and the code audit reading an .xlsx

Type: task
Status: resolved
Blocked by: 14
Size: M

## Question

The user (2026-10-28), grilled the same day: Copilot should turn a person's Excel workbook into
Hive, so "others can take over their work without getting me as involved in being 'the doer'".
They ship a template that forces a legible layout, the Formula workbook, built on dev with a
library main never installs: "I can accept new libraries in the dev branch that aren't ported
over to main. Create the template and maintain in dev, port over the one file on main export
that can't be recreated from main code." It holds the Tables and nothing a person could
half-edit: "template tables, leave the code cells blank since that just enables user error".

The code audit reads every file as UTF-8 and would flag the .xlsx, a zip. It learns to read
inside one rather than exempting it. The user: "no macros".

## Done when

- `openpyxl`, and the one package it needs, are pinned in `requirements-dev.txt` only. The pins
  test still holds `requirements.txt` to the libraries the Toolbox imports, and CI installs
  them through `requirements-dev.txt`, as it does for pytest.
- A dev tool, beside `tools/copilot_files.py`, builds `copilot/formula_workbook.xlsx`:
  - a first sheet of plain-text steps for moving a presentation workbook into this layout:
    paste a sample of raw data as values, Ctrl+T, keep the Table's own name, rewrite each
    formula once in the first row by column name, move fixed cells into `Parameters`, fill
    `Keys` only for a column with a typed-over cell, and take out anything not to be converted;
  - an empty `Parameters` Table (`name` | `value`) and an empty `Keys` Table (`table` |
    `key_columns`);
  - no data Table, no formula, no M, no macro.
- A test holds the committed .xlsx to what the tool builds, comparing its sheets, Tables, headers
  and cells, not its bytes: a zip's timestamps change with every build.
- `tools/code_audit.py` opens an .xlsx as a zip and reads each XML part as text, with the
  checks every other file gets. It refuses a workbook holding macros (`vbaProject.bin`, an
  `.xlsm` content type), data connections (`connections.xml`, query tables) or links to other
  workbooks (`externalLinks/`). `tests/repo/test_code_audit.py` has a sample workbook for each
  refusal, built in the test, and one clean one.
- `tools/offline_policy.py` reads the .xlsx's XML parts too, so a URL in one is found.
- `tools/export_clean.py` copies the .xlsx to main unstamped, as it copies the .txt files, and
  `tests/repo/test_export_clean.py` expects it.
- CONTEXT.md's **Formula workbook**, written while grilling, was committed ahead of this ticket
  (6cb93c0), to close D293.
- CLAUDE.md's Definition of done, the beginner reader included: the steps sheet is something a
  beginner reads.

## Answer

Built 2026-10-28. `tools/formula_workbook.py` builds `copilot/formula_workbook.xlsx` with
openpyxl 3.1.5 (and et-xmlfile 2.0.0), pinned in `requirements-dev.txt` only;
`tools/copilot_files.py` runs it with the text files. The workbook holds a Steps sheet and
the `Parameters` (`name` | `value`) and `Keys` (`table` | `key_columns`) Tables, each one blank
row under its headers, since Excel needs one. The export copies it byte for byte, and
`tests/test_formula_workbook.py` compares it with what the tool builds by sheets, Tables and
cells.

Settled while building:

- **It's "the empty Formula workbook", not a template**: CONTEXT.md's Template is the shape of
  a user's script (the drift review's D295).
- **The offline policy does the refusing, not the code audit.** A macro, an embedded object or
  control, a macro-enabled workbook, a data connection, a query table, a Power Query, a link to
  another workbook, any relationship out of it, a `WEBSERVICE`/`HYPERLINK`/`FILTERXML`/`RTD`/
  `IMAGE` formula, and a URL typed in a cell or formula: each is a finding of
  `offline_policy.workbook_findings`. That way the export, which reads the Clean tree with the
  offline policy, refuses them on main too. The code audit reads each part inside a workbook
  as a file of its own (`w.xlsx/xl/sharedStrings.xml`), for hidden text and encoded runs, and
  its command line runs the offline policy, which a test holds. "A URL in one is found" became
  "a URL a person typed": every part holds its XML namespaces' `http://` URIs, which nothing
  fetches.
- **The hook doesn't read workbooks**: it judges an edit's text, and no edit writes a workbook,
  so `READ_FILES` stays text files and `scan` adds `WORKBOOK_FILES`.

Reviews, on a3f8fc6:

- **Standards** (review-standards): no hard violation. Fixed: `get_column_letter`, a Table's
  range from its headers, a `Contents` type for `contents()`, `zipfile` imported at the top of
  the tests. Kept: `copilot_files.main()` building the workbook too, so one command writes
  `copilot/`; `Parameters`, which the glossary avoids only for a Session setting.
- **Spec** (review-spec): the refusals sit in the offline policy, as above; the single-quoted
  `TargetMode`, case in part names, and formulas or cells that link out are now found.
- **Beginner reader** (beginner-reader, opus), advisory. Its costliest three, each fixed in the
  steps: paste only the columns that hold data, not formulas (step 1); find typed-over values in
  the original and type them back, with an example Keys row (step 10); rebuild a summary block
  or PivotTable as a Table of its own (step 5). Also taken: do every source Table first (step
  3), clicking a cell writes `[@units]` (step 4), a number inside a formula is a fixed value
  (step 6), Power Query is optional and its Table converts (step 7), what can't convert (step
  8), taking things out comes before Keys (steps 9, 10), older Excel's Design tab, no spaces in
  a Table name, and what Hive is. The user decides on these: each is in `STEPS`.
- **Drift**: D294 (the export's docstring) and D295 ("template"), fixed in the commit after.
