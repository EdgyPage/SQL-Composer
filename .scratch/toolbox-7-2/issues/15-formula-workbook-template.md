# The Formula workbook template, and the code audit reading an .xlsx

Type: task
Status: open
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
- CONTEXT.md's **Formula workbook**, written while grilling, is committed with this ticket.
- CLAUDE.md's Definition of done, the beginner reader included: the steps sheet is something a
  beginner reads.
