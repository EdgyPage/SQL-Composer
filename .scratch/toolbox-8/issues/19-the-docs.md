# The docs and the Copilot files

Type: task
Status: open
Blocked by: 18
Size: L

## Question

Everything a user reads, brought to 8.0: the Workflows as the way to do each job.

## Done when

- The README (`docs/clean-branch-readme.md`) starts each job from its Workflow notebook and
  `do_next()`, and has a Conversion step in its numbered steps.
- How-to 27 becomes a script batch: several scripts, a CTAS, a temp table, a multi-insert, a
  self-reading table, renamed into dev, compared, promoted. Other how-tos and Worked examples
  that name a retired call follow.
- Each Workflow's how-to is generated from its step list in `workflows.py`, as its notebook
  is, and a test holds both to the list (moved here from ticket 12).
- The Intermediate Example project shows a finished Conversion in the new layout.
- Copilot file 07 says to run the convert Workflow for any script, of any length, and its tasks
  in `tools/copilot_eval_tasks.py` follow; the held-out score is taken once, recorded in
  `.scratch/copilot-eval/results.md`.
- The beginner reader has run on every changed page, its report linked here.
