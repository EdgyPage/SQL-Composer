# The Lineage state compares logic, never values, and a Toolbox rewrite is never an Own change

Status: accepted 2026-11-17, to be built by Toolbox 8.8

The user: "It often happens that changes in one upstream table in some calculated column
affects the effective logic of a downstream table ... the sql remains the same but the table
columns upstream may have changed." 8.8 adds the Lineage state, `admin/lineage/lineage_state.csv`,
which records each column's own logic and Effective logic, a row each time one changes, and the
Lineage difference, which reads it.

Whether a column "changed" is decided by comparing a fingerprint of its logic from one
recording to the next. What goes into that fingerprint is the decision here, and it is hard to
reverse: once a Project holds months of rows, a new way of fingerprinting makes every column
look changed at once.

## Decision

- **Logic, never values.** A column's own logic is the Hive the Toolbox writes for it and for
  the rows that count for it, with table aliases replaced by table names. A Run value is
  written as its function and what it was given, never the value it gave; a Hivevar as its
  name. So the build that runs each day, with a new date in it, is no change.
- **Recording never reaches the warehouse.** Each Statement is built with each Run value given
  a stand-in, never called, so a recording needs no `connect(...)` and runs inside any Project
  action, a Table notebook's `export_hive()` or an Upgrade.
- **Opaque steps count whole.** An Unchecked statement's or Unchecked derived table's text, or a
  Python step's function source, is one fingerprint, and a change to it is a change to every
  column the step writes.
- **A Toolbox rewrite is never an Own change.** A later Toolbox version, or a new sqlglot pin,
  may write the same logic as different Hive. Each row carries the Toolbox version that
  recorded it, and the recording an Upgrade makes marks each change it finds `toolbox`, never
  `own` or `inherited`. The Lineage difference folds those under the Upgrade, and from there
  fingerprints compare as before.

## Considered

- **Fingerprinting the user's Python call text** instead of the Hive: stable across Toolbox
  versions, but it changes whenever the user restyles code that writes the same Hive, and it
  misses what a Building block's change does to the Hive.
- **Fingerprinting the Hive as sent, values and all:** every Run value's new date would be a
  change every day, and recording would need the warehouse for each Run value that reads it.
- **Accepting a wave of false changes at each Upgrade:** a difference spanning an Upgrade would
  bury the user's real changes under the Toolbox's.

## Consequences

- A change in what a Run value's function gives is not seen; a change to the function, or what
  it is given, is.
- Every Upgrade records, so each version starts its own baseline, and the CSV can always be
  replayed to any point.
- Changing what goes into the fingerprint later needs an Upgrade that records with `toolbox`,
  as any rewrite does.
