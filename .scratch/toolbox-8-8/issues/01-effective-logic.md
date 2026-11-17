# Effective logic

Type: task
Status: resolved
Blocked by: -
Size: L

## Question

Today a Statement's Lineage stops at each Saved table it reads. 8.8 follows each column up
through every Saved table's own write, down to the tables the Project doesn't write (Q1), and
fingerprints what it finds so two recordings can be compared (Q2, Q3, ADR 0015).

## Done when

- **A new `lineage_state.py`** (in `tools/toolbox_registry.py`) works out, for a Project, every
  recorded column (Q4): each Saved table's `write()` columns, each Scheduled run's Statements
  (a SELECT named `<run>.<result>`), and each Table reference's columns for the tables the
  Project doesn't write.
- **For each column:**
  - its own logic: the Hive the Toolbox writes for it, with table aliases replaced by table
    names, a Run value as its function and what it was given, a Hivevar by its name;
  - its rows that count: WHERE, JOIN ON, GROUP BY and HAVING on its way to the output, as
    `lineage.py` already gathers them, written the same way;
  - the columns it reads, as `<db>.<table>.<column>`;
  - an own hash (its own logic and rows that count) and an effective hash (its own hash and the
    effective hash of each Saved table's column it reads), so a change anywhere upstream
    changes the effective hash only.
- **Opaque steps** (Q3): an Unchecked statement's or Unchecked derived table's text, or a Python
  step's function source, is one fingerprint shared by every column the step writes, marked
  opaque.
- **No warehouse** (Q6): each Statement is built with each Run value given a stand-in, never
  called; a test holds that working out the Example project's columns calls neither `query`
  nor `execute`, with no `connect(...)`.
- **A table or run that doesn't build** (Q19) is given back as not built, with why, and the
  rest is worked out.
- Tests: a filter changed upstream changes the downstream column's effective hash and not its
  own; an alias renamed changes neither; a Run value's new value changes neither, its new
  argument both of its own column; a retyped Table reference column changes the effective hash
  of each column reading it.

## Answer

Built 2026-11-17, on its own branch beside ticket 02, against the interface the two share.

- **`sqlglot_composer/effective_logic.py`** (in `tools/toolbox_registry.py`):
  `project_logic(root) -> ProjectLogic`, with `ColumnLogic` and `ProjectLogic` and the kinds
  `SAVED_TABLE`, `SCHEDULED_RUN` and `REFERENCE` exactly as the interface gave them. Not public:
  ticket 02's `project.record_lineage_state()` calls it.
- **What it reads:** each Table folder's writes through `project_lineage.project_tables`
  (`project.load`, as run_tables reads them), and each Scheduled run through `built_run_of`, as
  `export_project_lineage` builds it, with its parameters' defaults. A run's SELECTs are
  `<run>.<result>`; a write the build added from a Table folder is that folder's. Each Table
  reference the Reference sheet can read, for a table nothing in the Project writes, is a root:
  `project.reference_columns(path)`, new, reads it without running it.
- **Own logic:** each output's calculation written by `hive_text` with each table's column as
  `<db>.<table>.<column>`, each Derived table's column written out in its place (brackets only
  around a calculation), a Stack as `UNION_ALL(...)` of its Statements' columns, an aggregate
  with `GROUP BY ...`, a Run value as `run_value(<module>.<function>(<arguments>))` and a
  Hivevar as `'${hivevar:NAME}'`. So an alias or a Derived table renamed changes nothing.
- **Rows that count:** the write's INSERT OVERWRITE or INTO, SELECT DISTINCT, then each
  condition `lineage.deciding_boxes` (new, the report's `_deciding`) finds upstream, as
  `WHERE: ...`, `JOIN ON: ...`, `HAVING: ...`, `LIMIT ...`. Each condition box now carries a
  `logic` fact, `lineage.ConditionLogic` (its clause, its step, its tree, its `then`), so its
  Hive is written out in its own step's terms; nothing drawn changes.
- **Reads:** every table column the own logic and the rows that count name, group-by columns
  included. An Unchecked statement's or Unchecked derived table's text names tables only, so it
  reads `<db>.<table>.*`, every column of that table (`WHOLE_TABLE`, a deviation the
  `ColumnLogic` docstring now says).
- **Hashes:** the own hash fingerprints the own logic and the rows that count (SHA-256, 16 hex
  digits); a Table reference column's own hash fingerprints its type, which is how a retyped
  root reaches what reads it. The effective hash fingerprints the own hash and the name and own
  hash of every column upstream, followed through `reads`, so it doesn't hang on the order the
  columns are met in, and a table reading itself is no trouble. A Saved table's type isn't in
  its own hash: ticket 02 compares the `type` field.
- **Opaque steps:** an Unchecked statement's text, or a Python step's place and function
  source (a fingerprint of its compiled code where Python can't find the source, as for one a
  logic cell defines), is the own logic of every column it writes, `opaque=True`. A column
  reading an Unchecked derived table holds its text and is opaque too. Several writes of one
  table join their logic, reads and rows.
- **No warehouse:** `run_values.stand_ins()`, new, makes every Run value give a stand-in by
  its function's return hint (a date, else 0, False or `'1970-01-01'`), its function never
  called; `project_logic` runs within it and within the Project's folder.
- **`blocks_of`:** each Building block a Table notebook's logic cell imports, named by its path
  below `building_blocks/` without `.py` (`owner_on_day`, `prod/owner_on_day`), only those whose
  file is there.
- **Not built:** a Table folder passed over or a run that doesn't build is in `not_built`, by
  its name, with `project.one_line_message`'s why.
- **Tests:** `tests/test_effective_logic.py`, 12: a filter changed upstream changes only the
  effective hash downstream; an alias renamed changes neither; a Run value's function is never
  called, its new value changes neither hash, its new argument both of its own column; a
  retyped Table reference column changes the effective hash of each column reading it; Derived
  tables, a Stack and an Unchecked expression written out, a Derived table renamed changing
  nothing; an Unchecked statement and a Python step each one opaque step; a table that doesn't
  build noted; the Intermediate Example project worked out with no connection, its Scheduled
  run's SELECT among the columns; its Building blocks named; a Building block changed changing
  the tables importing it. `tests/snapshot/known.txt` is written again for the Hive the own
  logic makes.

## Comments

**Code review, 2026-11-17**, of tickets 01 to 06 together (3daf6b09..973594c2), its two axes
on Sonnet, recorded in the ledger as round toolbox-8-8-01-06. Fixed in 3d4a9bac:
- Standards: a whole-table read's expansion was written twice (`lineage_state._each_column`,
  `lineage_difference._reads_of`), now `effective_logic.each_column` and `column_key`;
  `CHANGES_AT_THE_COLUMN` repeated `ROOT_CHANGES`, now gone; `_recorded`, a vague name, is
  `_unrecorded_lines` and `_report_once_recorded`, which builds the call the five actions on
  names each built; a table's change words and box kind come from one map each.
- Spec: `building_blocks/prod/` wasn't hashed, so a prod copy's own change named no block;
  it is now, as `prod/<name>`.

Answered, no change:
- `because` names every changed column up the chain, nearest first, not only the farthest:
  each is a column the inherited change comes from, which the difference's chains need.
- "No Lineage state yet" waits for `admin/lineage.ipynb`: ticket 07 writes it.
- Recordings in one second: `_recorded_at` gives every recording, `export_hive()`'s too, its
  own second. A bumped time can be a few seconds after the clock, so a write in those seconds
  reads as before the change: a few seconds' slack, kept.
- An opaque step's readers show `inherited`: their own logic is unchanged, as Q3 and the
  Inherited change's definition say.
- `since=` before the first recording starting from it, and Building block rows in the one CSV,
  are the ticket changes each Answer records.
- The smells left: the `before` and `rows` pair (a `Recording` type), `record` returning
  text that `record_lineage_state` compares, the Middle Men `deciding_boxes` and `_columns`, and
  `difference(call=...)`'s default. Judgement calls, left for a refactor with no version raise.
