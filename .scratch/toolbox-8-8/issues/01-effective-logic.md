# Effective logic

Type: task
Status: open
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
