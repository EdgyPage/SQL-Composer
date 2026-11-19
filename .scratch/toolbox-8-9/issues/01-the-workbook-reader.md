# The workbook reader in the Toolbox's folder

Type: task
Status: resolved
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

## Answer

**Built.** `sqlglot_composer/workbook_reader.py`, standard library only, is the one reader of a
workbook. `read_workbook(path or bytes)` gives a `Workbook`: its `sheets` (each a `Sheet` with
its `tables`, its other `cells` by (row, column), its `charts` and its `pivot_tables` count), its
`defined_names` (each name to what it stands for), its `queries` (each a `Query`: name, M, the
Table it loads) and its `order`, a dict from each `Piece` (kind `EXCEL_TABLE` or `POWER_QUERY`,
and name) to the pieces it reads, each after every piece it reads; a loop raises `LoopError`,
its message as before. A `Table` has its name, ref, `columns`, `has_total_row` and
`loaded_by`; each `Column` its `header`, its `kind` (`TYPED`, or `FORMULA` when any row holds a
formula, a value typed over one among them), its `cells` below the header (a formula as "="
and the text the workbook saves) and its Total Row's `total`. Also in the file: `coordinate`,
`piece_name`, `shifted_formula` (was `_shifted`, a name another Toolbox file's private function
has) and `section_queries`. No Toolbox public name: `__init__` doesn't import the file.

`copilot/workbook_text.py` keeps only the text: `as_typed`, `cell_text`, `as_text`,
`workbook_text`, `main`, writing byte for byte what it wrote (the three fixtures' `.txt`, and
every Excel evaluation task's text against openpyxl's view, pass unchanged). `LoopError` is
still reachable as `workbook_text.LoopError`, which `tools/workbook_fixtures.py` uses.

**The by-path load, decided.** `workbook_text.py` puts the Toolbox's folder beside its own,
`../sqlglot_composer`, first on `sys.path`, imports `workbook_reader` by name, and takes the
folder off the path again (try/finally); a missing reader is a three-part refusal. Why not
`importlib.util.spec_from_file_location`: the offline policy reads it as dynamic code, and in
`copilot/`, user-copied code, nothing may be allowed (the offline hook refused it on a trial
file), whereas a plain import after a path entry is no finding. The folder is on the path only
while the reader loads, so the Toolbox's other files aren't importable by name in whatever
imports the script (the tools, the tests). Since the folder stands first while it loads, a
Toolbox file named as one of Python's own modules would stand in for it: a test holds that none
is.

**The registry.** `tools/toolbox_registry.py` names `workbook_reader.py` in `PYTHON_FILES`, and
records `WORKBOOK_READER` and `WORKBOOK_READER_LOADED_BY = "copilot/workbook_text.py"`.
`may_import(WORKBOOK_READER)` is empty (not even pandas), and `imports_outside` also lists any
relative import in the reader ("workbook_reader.py imports .tables"), as it is loaded alone;
every other file's imports are held as before. A test holds that the registry's file is the only
one in `copilot/`, `tools/`, `worked_examples/` and the Example database that imports the
reader.

**The export** carries both with no change to `tools/export_clean.py` (the folder's files come
from the registry; `copilot/` is copied whole). A test runs main's `workbook_text.py` from the
built Clean tree in a fresh Python with `sqlglot` and `sqlglot_composer` both blocked in
`sys.modules`, through `export_clean.fresh_python` (already allowed), and gets the fixture's
text.

**Left for the user: one code audit entry.** The DataMashup's base64 decoding moved with the
reader, so `tools/code_audit.py` finds `sqlglot_composer/workbook_reader.py:21 encoded payload:
imports base64`, and its entry for `copilot/workbook_text.py` ("imports base64", the user's OK
2026-11-01) is stale. The fix is to move that entry to the reader's path, with the same reason,
once the user OKs the Toolbox's folder holding the decoder (ADR 0016 moves the reader there).
Until then `tests/repo/test_code_audit.py::test_the_repo_reads_clean` fails.

Also for the user: `workbook_text.py`'s docstring now says it reads with the Toolbox's reader,
beside the copilot folder, and it has a new refusal for when that folder isn't there; a user who
copied the script alone, out of the download, now needs the `sqlglot_composer` folder beside its
folder. Both are things a beginner sees, so the beginner reader should run on them.

**The code audit entry, done.** The user's OK, 2026-11-19: the entry moved to
`sqlglot_composer/workbook_reader.py`, its reason kept and the move noted; the audit reads
clean.

## Review

The code-review skill, 2026-11-19, on 4d430ccc (Standards and Spec, on Sonnet). No hard breach.

- **Spec: "loads that file by its path".** It puts the folder first on `sys.path` and imports
  the reader by name, then takes the folder off: `spec_from_file_location` is dynamic code the
  offline policy refuses in `copilot/`, where nothing can be allowed. The effect the ticket asks
  for holds (the Toolbox's `__init__` is never imported, nothing but Python is needed); the
  wording is closer than the mechanism. Kept, and told the user.
- **Spec: the third fixture pinned.** 03_loop's reader data is its refusal, pinned by
  `test_a_loop_is_refused_naming_each_link_in_excels_words`.
- **Spec: charts in the reader's data.** The old script read them too (its "left alone" list);
  kept, as the text holds them.
- **Standards: `_formulas` and `read`.** Renamed `_formulas_text` and `reads`.
- **Standards: `_take_sheet_queries` changes the sheets it is given and returns the queries.**
  Kept: "take ... off its sheet" says both, and its docstring says so.
- **Standards: a hand-joined list in the reader.** The reader may import only the standard
  library, so `shared.in_words` is out of reach; answered by the registry's rule.
