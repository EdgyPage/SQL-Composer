# The docs and the Copilot files

Type: task
Status: open
Blocked by: 02, 03, 04, 05, 06, 07, 08, 09, 10, 11
Size: M

## Question

8.1 changes what a user does in every Workflow but upgrade.

## Done when

- `docs/workflows.md` and the README's charts, drawn again; the README's steps, the how-tos,
  how-to 29 most, the Worked examples and the Example projects, each Workflow notebook with its
  decisions cell; Copilot file 13, and any other naming a step that changed.
- Every Copilot file is read again as one story, file 00 to file 13: the same names, the same
  steps in the same order as the Workflows and the README, each file pointing to the one that
  takes over, and nothing left of a step 8.1 removed (a box ticked by hand, a Table reference
  typed, the SET lines sent by hand). Each listed step is generated from the Workflows where it
  can be, and held by ticket 01's one-source test where it can't.
- The Copilot files' own tests pass: every file at most 8,000 characters, every code block
  runs, every name is real.
- The beginner reader runs on the README, the Workflow how-tos and Copilot file 13, and its
  report is linked.
- The held-out Copilot evaluation runs on every Copilot file 8.1 changed, file 13 with its
  Workflow tasks, and the Excel evaluation if files 11 or 12 changed; each score is recorded in
  `.scratch/copilot-eval/results.md`, at least what 8.0's was.
