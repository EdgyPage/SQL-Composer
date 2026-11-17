# The Lineage state

Type: task
Status: resolved
Blocked by: 01
Size: L

## Question

Where ticket 01's columns are kept, one recording after another, so a change is found without
parsing HTML (Q5, Q7, Q11 to Q13, Q19, Q23, Q25).

## Done when

- **`project.record_lineage_state()`**, a Project action in the Admin log, takes nothing,
  works out the whole Project (ticket 01) and adds to `admin/lineage/lineage_state.csv` a row
  for each column that changed since the last recording, never rewriting a row. The first
  recording writes every column as `first`.
- **Its columns**, in this order: `recorded_at, commit, recorded_by, toolbox_version, table,
  column, kind, change, type, own_logic, reads, rows_that_count, own_hash, effective_hash,
  because`, as the map's Notes say.
- **`change`:**
  - `added` and `removed`; `removed` only from `remove_table` and `remove_scheduled_run`, never
    from a table that didn't build, whose last rows stand (Q19);
  - `own`: the own hash changed; `inherited`: only the effective hash did, `because` naming
    the root columns whose `own` (or `retyped`) change it comes from;
  - `retyped`: a Table reference column's type (Q12); a description, an Alias, the Key, the
    Partitions or the location never counts;
  - `opaque`: an opaque step's fingerprint (Q3);
  - `toolbox`: any change found by a recording an Upgrade makes, never `own` or `inherited`
    (Q23, ADR 0015).
- **Building blocks** (Q25): each recording keeps each `building_blocks/` file's hash beside the
  CSV; an `own` change in the same recording as a change to a block the table imports has
  `because` `building_block:<name>`.
- **Renames** (Q13) are `removed` and `added` upstream and `own` downstream.
- **It prints one line**: "Lineage state: 3 columns changed (1 own, 2 inherited):
  project.export_lineage_difference() shows them.", or "no change", and names each table or
  run not recorded, with why.
- `commit` is read as `lineage.scripts_commit` reads it, blank outside git; `toolbox_version`
  from `version.txt`.
- It never reaches the warehouse (Q6); in `public.py` with a docstring and its example.
- Tests: replaying the CSV to any recording gives that recording's columns; two recordings with
  nothing changed add no row; each `change` is shown arising.

## Answer

Built 2026-11-17, against ticket 01's interface (`effective_logic.ColumnLogic`,
`ProjectLogic`, `project_logic`), built at the same time on another branch.

- **`sqlglot_composer/lineage_state.py`**, in the registry, a pure core over a `ProjectLogic`:
  - `record(root, logic, recorded_by, by_upgrade=False) -> list[str]` adds a row to
    `admin/lineage/lineage_state.csv` for each column, and each Building block, that changed
    since the last recording, writing the header when the file is new, never rewriting a row,
    and gives back the lines a Project action prints;
  - `read_rows(root) -> list[dict[str, str]]` reads the file, oldest first;
  - `columns_at(rows, recorded_at=None) -> dict[tuple[str, str], dict[str, str]]` replays it
    to any recording: each column's last row then, a removed one gone;
  - `STATE_FILE`, `STATE_COLUMNS`, the change words and `NO_CHANGE`.
- **The columns**, in order: `recorded_at, commit, recorded_by, toolbox_version, table,
  column, kind, change, type, own_logic, reads, rows_that_count, own_hash, effective_hash,
  because`. `reads` is `;`-separated; `commit` is `lineage.scripts_commit`'s, empty outside git
  (its `nogit` and `nocommits`); `toolbox_version` is `TOOLBOX_VERSION`, from version.txt.
- **The change rules**, in this order: a column not in the last recording is `added`; a Table
  reference's column whose type changed is `retyped` (its logic is its type, so its type is
  looked at first); an own hash changed is `own`, or `opaque` for an opaque column; a type
  changed is `retyped`; an effective hash changed alone is `inherited`. The first recording,
  one with no row before it, writes every column and block `first`.
- **`because`:** an inherited change names, as `<db>.<table>.<column>` joined by `;`, every
  column up its chain, nearest first, with an `own`, `opaque`, `retyped`, `added` or
  `removed` change in the same recording; an own or opaque change names
  `building_block:<name>` for each block its table imports (`blocks_of`) that changed in it.
- **Removed:** a column gone from a table that still builds; and every column of a table, or
  of a Scheduled run's Statement (`<run>.<result>`, by its run), the registry marks removed,
  its Table folder, Table reference or Scheduled run. A table in `not_built`, or gone with no
  registry removal, keeps its rows, and the report names it, with why or with the Project
  action that marks it removed. A removed row repeats the column's last values.
- **Building blocks (a change to the ticket):** each `building_blocks/*.py` file's hash is kept
  as rows of kind `building_block` in the same CSV, its name in `table`, `column` empty, not in
  a file beside it, so the one file replays whole. The hash reads `\r\n` as `\n`, so a
  checkout on another computer hashes the same. `building_blocks/prod/` isn't read: a prod
  copy's own change names no block yet.
- **An Upgrade's recording** (`by_upgrade=True`) marks each change `toolbox`, its `because`
  empty, but a removal, which the replay needs as it is; an Upgrade's first recording is
  `first`, as ticket 10 wants.
- **The report:** "Lineage state: the first recording, N columns of M tables, in
  admin/lineage/lineage_state.csv."; "Lineage state: no change since the last recording.";
  "Lineage state: 3 columns changed (1 own, 2 inherited): project.export_lineage_difference()
  shows them.", counting own, inherited, retyped, opaque, added, removed and toolbox in that
  order; "Building blocks changed: ..."; and a "Not recorded, its rows from before kept: ..."
  line for each table or run not recorded.
- **`project.record_lineage_state()`**, in `project.__all__` (the project module's names live
  there, not in `public.py`, and `tests/repo/test_toolbox_checks.py`'s `PROJECT_NAMES` names
  this ticket), works out `effective_logic.project_logic(root)`, records with `recorded_by`
  `project.record_lineage_state()`, and logs itself in the Admin log, its Files line
  "added to admin/lineage/lineage_state.csv", or none changed. Its docstring and example, a
  Project just started, are in the Example gallery; the project module's docstring names it.
- **Tests:** `tests/test_lineage_state.py`, 17, driving `record` with columns written out:
  the first recording; no row when nothing changed; own upstream and inherited downstream;
  a retyped root inherited by each reader; a root two tables up; opaque; added and removed;
  a rename; a table and a Scheduled run removed by the registry; one not built and one gone
  by hand kept; a Building block named; line endings; an Upgrade's `toolbox`; the replay to
  each of three recordings; and the logged Project action, its `project_logic` patched. The
  end-to-end test on the Example project waits for ticket 01's merge. The snapshot gained the
  three report lines.

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
