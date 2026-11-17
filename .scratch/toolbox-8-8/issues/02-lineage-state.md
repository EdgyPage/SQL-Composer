# The Lineage state

Type: task
Status: open
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
