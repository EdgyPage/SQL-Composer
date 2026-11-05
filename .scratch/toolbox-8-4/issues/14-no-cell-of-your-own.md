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
