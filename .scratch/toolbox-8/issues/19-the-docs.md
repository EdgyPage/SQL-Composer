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

## Answer

Built in parts, each its own commit.

### The flow charts (19a)

- `tools/workflow_graph.py` writes every chart a user reads, from `workflows.py`'s step lists:
  each Workflow's, as before, and two more, kept as constants in the tool: the program flow,
  the Toolbox's own path from a Table reference through Clause functions, a Statement, the
  Guards and Load limits and to_hive, to run_query or run_execute through warehouse.py, with
  where a Saved table's notebook and a Conversion join it; and the Excel flow, from a Formula
  workbook through Copilot files 11 and 12, Hive, the convert Workflow, dev, compare and
  promote. Each is a fenced `mermaid` block beside the same steps as a numbered list, each
  step's kind in words and its call under it (`steps_listed`, which the Copilot files take
  alone).
- The README template, `docs/clean-branch-readme.md`, gains "The Workflows": the program flow
  and each Workflow's chart, between `<!-- chart: NAME -->` markers the tool fills; the Excel
  flow sits in "Have Copilot write it".
- How-to 29, "Follow a Workflow" (`worked_examples/how_to/29_follow_a_workflow.py`), is written
  whole by the tool: the imports each Workflow notebook starts with, then per Workflow its
  chart, its names cell and its steps, so each Workflow's how-to is generated from its step
  list, as its notebook is. The how-to page and the Example gallery show a fenced Mermaid
  chart as its text (`example_gallery.is_chart`); a test holds the README's charts and how-to
  29 to what the tool writes.
- Settled here: a chart a user reads names each step without its call, which the list beside
  it gives, as a call on several lines can't sit in a Mermaid label; docs/workflows.md keeps
  the calls in its labels. Three step names were shortened to fit a chart's line, their
  detail moved to their calls.
- D351 fixed here: CHANGES names `project.table_reference`. The send step of
  change_a_saved_table names a check after it, such as admin.check_the_copy, which
  move_to_own_folder needs.

### The README and the how-tos (19b)

- The README template is a tutorial in nine steps: its opening says each job has a Workflow
  notebook, which `project.check()` and `project.do_next()` take you through; steps 2 and 6
  start from the references and new_table Workflows; step 8 names `do_next()`; and step 9,
  "Convert someone else's Hive", is the convert Workflow, from a batch of scripts to compare
  and promote.
- How-to 27 is now how-to 9, the last Getting started how-to, so the README's step 9 is it, as
  `test_readme_step_n_is_getting_started_how_to_n` holds; the Intermediate how-tos after it
  are each one number on, 10 to 27, links being by name. It is rewritten as a batch on a copy
  of the Starter Example project: two scripts, a temporary CTAS, a FROM with two INSERTs, an
  INSERT INTO that reads its own table (seeded), a rename, the checklists, create, seed and
  write in dev, compare, and promote, which refuses until each compare passes. The Example
  database holds no Dev Database, so its compare says so; the page says what passes at work.
- No other how-to, Worked example, Example project README or docstring names a retired call or
  path (admin/new_table.ipynb, admin/conversions/, finish_conversion): a grep found none.
- D352: a chart's list says each step's kind as its notebook does (`step_said`). D353: the
  Excel chart follows the README's Excel steps, five files and a Conversion per query, until
  19d changes both. D354: CHANGES names the charts and how-tos 9 and 29. D355:
  workflow_graph's docstring says what `steps_listed` gives.

### The Intermediate Example project's Conversion (19c)

- `tools/example_project.py` compares the Intermediate Example project's Conversion,
  team_failures, with its original, through a query that reads both as the rows the converted
  query gives (the Example database holds no Dev Database), so the batch is finished: its
  folder is in `admin/workflows/convert/finished/team_failures/`, and its table's
  `conversion/compare.md` says it passed, in place of the batch archived in admin/removed/.
  Its README says so. The Upgrade test counts the finished folder among what the Example
  project gained by hand since 7.2.
- D356: the README says `do_next()` runs the steps it can, up to the first it can't. D357: the
  Getting started summary, in the README and the how-to page, names a Conversion. D358: the
  README's list of what the Starter project lacks names the ops_reports batch. D359: tests
  name a how-to by its title, not its number.
