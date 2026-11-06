# Notebooks read top to bottom

Type: task
Status: resolved
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
Built 2026-11-05.

- `workflows.reads_straight_down(workflow)`: a Workflow with a names cell and a step that
  decides, which is convert, promote, new_table and references. Their notebooks
  (`notebook_cells`, `intended_path_cells`) open with the names cell, "Run up to your
  Decisions" (`run_cell_text` under that heading), the decisions cell, and "Run the rest",
  then "# Step by step" over each step's cell as before, `project.do_next()` last. Each other
  notebook ends with its run cell, as before.
- Their first cell (`_about_straight_down`, sharing `_about_text` with the rest) says the
  intended path first. `project.run_workflow` stopping says to run "Run the rest", the cell
  under the decisions cell, and its docstring names both run cells.
- **Found and fixed**: a step that writes the decisions cell's answers was done once no
  Decision was open. A "seed" answer, which no Decision asks for, was never written by the
  runner when the rest were answered: promote's prod seed copied every Partition. It is now
  done only once each seed limit is written too (`workflows._seed_written`, the seed filter
  moved into `decisions.seed_answer` so both share it).
- Tests: `tests/test_no_cell_of_your_own.py` (which notebooks read straight down; the intended
  path is the first code cells, in order, with no other run cell; its text sends you only down;
  the runner's stop sends you to the cell under the decisions cell); `tests/test_run_workflow.py`
  updated. The journeys skip the run cells when going step by step.
- **Count**: the user's batch converted and promoted, each notebook read top to bottom, **20**
  actions, from 01's 35 (`KNOWN_ACTIONS`); the step-by-step journeys stay as they were.
- The text test holds the intended path's cells, not the step-by-step section's: a step's own
  decision step still names "the decisions cell", above it, as running one step on purpose is
  the edge the docs teach (8.4's ticket 14).
