# No cell of your own: workflow and usability tests

Type: task
Status: open
Blocked by: 12
Size: M

## Question

The user (2026-11-05), partway through 8.4: "At the end of the ticket implementation, create
some new tests to add to the current suite of usability and workflow tests. I did notice
during my use that cells in the covert notebook had me jumping around between sections and
creating cells per the instructions. Ideally, a user does not need to create any cells for use
cases inside the documentation."

And: "As context, the cells were small eg create a cell for project.check(), etc. it was just
odd that the documentation on while on the intended path still needed me to create cells." So
the cells asked for are small calls a step's text names, such as `project.check()` to read the
open Decisions and the DECISIONS to paste: each belongs in the notebook, under the step that
names it.

And, after: "Keep documentation for edge cases, don't load the flows with effectively dead code
and cells. I prefer strong edge case documentation over a crowded user experience." So the
line is the intended path: every step of it runs in a cell the notebook ships, and nothing
more. An edge case (another Partition compared, a Run value that runs a statement of its own,
a table converted before 8.4) is taught in the docs, plainly and fully, and gets no cell or
input of its own unless the intended path needs it.

## Done when

- **A test reads every text a user follows** (each Workflow notebook's cells, `docs/workflows.md`,
  the README template, the how-tos, and the Copilot files that teach a Workflow) and finds no
  instruction to make a cell of one's own ("in a new cell", "add a cell", "make a cell", "a
  cell of your own"). Each place that says one today is mended so the step it describes has a
  cell the notebook ships, or an input of its names or decisions cell.
- **A test walks each Workflow notebook** and holds that every step a user runs has a code cell
  under its heading, and that each use the docs teach for that Workflow (8.3's PARTITION, 8.4's
  Run values, `all_tables` and seed limits among them) is reached through the cells shipped,
  their names cell and decisions cell alone.
- **A Run value needs no file of your own to start**: `project.start()` writes
  `building_blocks/run_values.py`, with one example function to change, as it writes
  warehouse.py, and the Upgrade step adds it to a Project that hasn't one; the decisions cell's
  comment names it.
- **Journeys**: the convert journey of the user's batch (01) runs through the runner too, and a
  promote journey of a seeded table limits its prod seed from promote's decisions cell.
- **The usability loop gains a scenario**: a zero-context run converts a batch whose Script tag
  is answered by a Run value and whose seed is limited, from what main ships, its record saying
  how many cells the run added (none, to pass). Its first round is run and recorded in
  `.scratch/usability-loop/results.md`, with what it found.

## Answer
Built 2026-11-05.

- **A cell for each decision step**: each Workflow's decision step that answers Decisions
  (convert's, promote's, new_table's and references') now has a `project.check()` cell under
  its heading (`workflows.DECISIONS_TO_ANSWER_CELL`), which names each open Decision and
  prints a whole DECISIONS to paste; its text opens "Run the cell below" (`RUN_THE_CHECK_CELL`).
  That was the cell the user made by hand.
- **The edge cases are the docs'**, as the user asked after: the references step's Key check
  says the code check_key takes, pointing to how-to 21, with no "new cell"; the upgrade's advice
  points to step 1's cell of the upgrade notebook, and says where a Project made before 8.0,
  which has none, runs it.
- **No file of your own to start a Run value, dropped**: a `building_blocks/run_values.py` in
  every Project would be the dead code the user asked to keep out; a Run value's function is
  taught in the docs (12), its file one the user writes when they need one.
- **`tests/test_no_cell_of_your_own.py`**: no notebook a started Project ships asks for a cell
  of your own; each call a Workflow step says to run has its cell; each step you run has a
  cell under its heading, a decision step its `project.check()`.
- **The runner reads a function answer**: `project.run_workflow` and check() read the decisions
  cell without running it; a cell that imports a Run value's function from the Project, such
  as `from building_blocks.run_values import period_end`, now gives it, its Project imports
  alone run as load runs a logic cell's (`workflows._decisions_assignment`), so the runner
  takes the same cell the notebook does.
- **Journeys**: the user's batch through the runner, and promote of its seeded table with the
  prod seed limited from promote's decisions cell, its prod rows the dev ones.
