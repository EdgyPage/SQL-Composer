# new_table: the Table reference from the logic

Type: task
Status: open
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
