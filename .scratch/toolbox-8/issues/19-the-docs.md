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
- Every Copilot file says 8.0's way, not only 07 (the user, 2026-10-31: "update the copilot
  files including the Excel conversion instructions"): 00, 01, 02 and 06 name the Workflow
  notebooks and `do_next()` where they name an admin notebook or a one-off call; 11 and 12,
  the Excel files, send the Hive Copilot writes from a workbook to the convert Workflow as a
  batch (`project.convert(name, files=[...])` or the Hive whole), with DEV filled in, in place
  of pasting each query; each stays under 8,000 characters, and
  `copilot/all_in_one/all_copilot_files.txt` is merged again.
- The README template's Excel section (its "Convert this workbook" steps) follows file 11.
- The Excel evaluation's tasks (`tools/excel_eval_tasks.py`) and the Copilot evaluation's
  follow the files; each held-out score is taken once and recorded.
- Every other page a user reads says 8.0's way: every how-to and Worked example, both Example
  projects' READMEs, the Toolbox's docstrings and refusals, CONTEXT.md, and the generated
  pages (how_to.html, examples.html); a test or a grep finds no retired call or path left
  (admin/new_table.ipynb and the rest, a Conversion "of one query" where a batch is meant).
- Flow charts a person and an LLM both read (the user, 2026-10-31: "I like the visual graphs of
  program flow and workflow graphs being human and machine legible"):
  - each Workflow's chart, as Mermaid text in a fenced `mermaid` block, which GitHub and VS Code
    draw and an LLM reads as text, beside the same steps as a numbered list: number, name,
    kind in words, its call;
  - a program-flow chart of the Toolbox's own path: Table reference, Clause functions,
    Statement, Guards and Load limits, to_hive, run_query or run_execute through warehouse.py,
    and where a Saved table's create() and write() and a Conversion join it;
  - an Excel chart: workbook, Copilot files 11 and 12, Hive, the convert Workflow's batch, dev
    tables, compare, promote;
  - in the README template and the how-tos users get on `main` (not only `docs/workflows.md`,
    which stays on dev), and in the Copilot files as the numbered list, which fits the
    8,000-character limit where a chart wouldn't;
  - generated from `workflows.py`'s step lists by `tools/workflow_graph.py`, never typed by
    hand, and a test holds every copy to what the tool writes.
- The beginner reader has run on every changed page, its report linked here.
