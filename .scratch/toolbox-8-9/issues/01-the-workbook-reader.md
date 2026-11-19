# The workbook reader in the Toolbox's folder

Type: task
Status: open
Blocked by: -
Size: M

## Question

Where the one workbook reader lives, so the Toolbox and `copilot/workbook_text.py` read a
workbook the same way (round 3, Q6; ADR 0016).

## Done when

- **The reader is one file in `sqlglot_composer/`**, standard library only: what
  `workbook_text.py` reads today (each sheet's Excel Tables, their typed and formula columns
  and Total Rows, the other cells, defined names, each Power Query's M from the DataMashup or a
  Power Query sheet, and the Order, a loop refused), given back as data, not text.
- **`copilot/workbook_text.py` loads that file by its path**, never importing the Toolbox (whose
  `__init__` checks sqlglot), so it still needs nothing but Python; it writes the same text.
- **The registry** names the new file and the one file outside the folder that loads it, and
  `imports_outside` still holds every other import.
- The main export carries both, and `workbook_text.py` run from main's tree, with no sqlglot
  installed, still writes its text.
- Tests: `tests/fixtures/workbook_text/` gives byte for byte the text it gives today; the
  reader's data for each fixture is pinned.
