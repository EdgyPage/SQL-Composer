# new_table: the Table reference from the logic

Type: task
Status: resolved
Blocked by: 04
Size: M

## Question

new_table asks for the Table reference by hand, then logic that must agree with it; the
logic's SELECT already names the columns (map, "new_table": Q8).

## Done when

- new_table's steps swap: the logic first, then a file step writes the Table reference from
  it: its columns from the SELECT, in order; each type from the Table references it reads, or a
  guessed-type Decision; `partitioned_by`; the Key (04); `location`, a Decision.
- A Table reference the user changed by hand is kept, as 03 says.
- Its journeys show it (`tests/test_workflow_journeys.py`, ticket 01): the new_table journey
  types no column or type.

## Settled with the user (2026-10-31)

The partition columns come from a line in the logic: the Saved table Template's logic cell
gains `PARTITIONED_BY = ["<PARTITION_COLUMN>"]`, beside READS, filled in with the logic. The
step that writes the Table reference reads it from there, with the columns and types from
preview() and the Key proposed as convert proposes it (04). (Asked: a line in the logic, or a
partitioned_by Decision in the decisions cell; the user chose the line.)

## Answer

Built 2026-10-31.

- **Steps, logic first:** new_table runs 1 make each Table folder; 2 write each table's logic
  (done when its preview() builds: `workflows.every_preview_builds`); 3 write each Table
  reference from its logic (`project.reference_from_logic(TABLES)`, a file step do_next and the
  runner run); 4 answer each open Decision in the decisions cell; 5 write each answer in; 6
  preview; 7 create and write.
- **new_table's reference** (the saved_table_reference Template) is a stand-in that imports,
  `columns={"<COLUMNS>": "string"}`, so the logic, which imports its own table, runs before
  the reference is written; `<COLUMNS>` is a placeholder Decision whose question names
  reference_from_logic (`decisions.COLUMNS`).
- **project.reference_from_logic** (public, new) runs the logic cell, builds preview(), and
  writes the reference as a Conversion writes one (`tables.table_reference_text`): each column
  preview() gives, in order, typed as the tables it reads type it, "string" as a guessed type
  where nothing tells; `partitioned_by` from the logic's `PARTITIONED_BY`, refused when it
  names a column preview() doesn't give; the Key proposed (04, with the partition columns);
  location a Decision. A reference whose columns aren't `<COLUMNS>` any more is kept, so the
  file is the user's once they write it (03).
- **Templates:** saved_table and quality_checks gain `PARTITIONED_BY = ["<PARTITION_COLUMN>"]`
  beside READS, filled in with the same placeholder; their text cell says to run
  reference_from_logic, not to fill in the reference.
- **Done-checks:** answered and made need the reference written from the logic first, else a
  location answered against new_table's stand-in would mark the step done and the runner pass
  over the logic steps before it.
- **Journeys:** the new_table journeys, both ways, type no column or type: the only hand edit
  left is the logic itself, what the user writes (KNOWN_FIDDLING keeps it); the location is
  typed into the decisions cell, and the Key comes from the proposal.
- **Tests:** test_workflow_steps (the logic step done once preview builds; the reference step
  once its columns are written, its docstring still naming <COLUMNS>; reference_from_logic
  writing the columns preview gives, and keeping one whose columns you wrote),
  test_project_templates (the stand-in a Table; the logic's partition columns and Key).
- **Upgrade:** a Project's admin/templates/ hold the Templates new_table copies; one still as
  7.2 or 8.0 wrote it is written again, one the user changed is marked
  (`upgrades._write_templates_again`, in the 8.0 step for now, since 8.0 never shipped:
  ticket 13 moves it to 8.1's). A Project's own Table notebooks are the user's and stay.
- **Code review:** Standards: the "columns written" check done three ways (now
  `decisions.has_columns_written`, which an older Template's <COLUMN> fails too),
  `preview_builds` a copy of `logic_loads` (one `_logic_builds`), the Key not through
  in_words, CONTEXT.md's Conversion line. Spec: a logic cell with no PARTITIONED_BY read as
  unpartitioned (now refused, as an older Template's logic has none) and partition columns
  not checked last (now checked); the docstring silent on write(); "Kept" with no way back
  (now says how); the Template rewrite untested (a test of the mark and the rewrite).
- **Beginner reader:** [08-beginner-reader.md](../reports/08-beginner-reader.md).
