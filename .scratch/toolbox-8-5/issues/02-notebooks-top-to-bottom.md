# Notebooks read top to bottom

Type: task
Status: open
Blocked by: 01
Size: M

## Question

"I want sequential steps without having to roll back up and down." (map, "Notebooks read top
to bottom").

## Done when

- **convert, promote, new_table and references** open with: the names cell; a "Run up to your
  Decisions" cell, `project.run_workflow(...)`, stopping at the first Decision and printing the
  DECISIONS to paste; the decisions cell, directly below; a "Run the rest" cell. Below, a "Step
  by step" section holds each step's cell, as 8.4's, each decision step with its
  `project.check()` cell.
- `project.run_workflow` stopping at a Decision prints, last, the whole DECISIONS and where it
  goes: the decisions cell below the one just run.
- change_a_saved_table and upgrade keep their step-by-step order.
- `tests/test_no_cell_of_your_own.py` holds that each of the four notebooks' intended path is
  its first four code cells, in that order, and that no text sends the user to a cell above the
  one it is under.
- The journey (01) runs the four cells, its action count falling.

## Answer
