# Decisions printed to paste

Type: task
Status: open
Blocked by: 03
Size: M

## Question

Answering step 2 today means running `project.check()` in a cell of the user's own, or opening
each table's `conversion/checklist.md`, then typing a dict from lines (map, Q22).

## Done when

- Step 1's output (`project.convert`, and new_table's step converting a query) and
  `project.check()` print the instance's open Decisions as one whole `DECISIONS = {...}`,
  ready to paste into the decisions cell: each table by its dev name, each value still to give
  `"<FILL IN>"`, a proposal where the Toolbox has one, and each tag's script and line in a
  comment beside it.
- A `"<FILL IN>"` pasted and left is no answer: step 2 isn't done, and step 3 writes nothing
  for it.
- It holds in every Workflow with a decisions cell: convert, promote, new_table and references.
- The Toolbox still never writes into the notebook (8.1's 02): it prints.
- Each journey answers its decisions by pasting what was printed and filling it in.

## Answer
