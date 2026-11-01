# The loop's harness: agents, relay, workspace, scoring

Type: task
Status: open
Blocked by: -
Size: L

## Question

Nothing tests whether a person with no context can follow the Workflows, or the Excel path, from
what main ships (map, "The loop": Q4, Q8, Q9, Q11).

## Done when

- A tool on dev, `tools/usability_loop.py`, that for one scenario and one run:
  - builds the Clean tree into a temporary folder with the export's own builder, and a Project
    there whose warehouse.py sends to a warehouse that keeps each write
    (`tools/workflow_warehouse.py`), holding the scenario's starting tables and originals;
  - writes each agent's message: its role (a zero-context technical user; a zero-context
    non-technical user; a fresh converter), its job in the user's words, and what it may read,
    the Clean tree alone;
  - relays a stuck agent's question to a fresh Copilot stand-in, loaded with file 00, then the
    file 00 names, at most five a run, each kept in the run's log;
  - scores the run's end against the scenario's answer key: the tables, their rows, the files a
    Workflow's end goal holds; and, for an Excel scenario, each final Table's Saved table
    against the workbook's own values, as `tools/excel_eval.py` reads them;
  - records the run under `.scratch/usability-loop/runs/<date>-<scenario>-<n>/`: every message,
    answer, question and the score, and one row in `.scratch/usability-loop/results.md`.
- Agent definitions in `.claude/agents/`, each on Haiku: the user roles, which may read and
  write in the run's folder alone, and the Copilot stand-in, `copilot-proxy`, as it is.
- `docs/usability-loop.md` says how a round is run, from this session or by hand.
- Tests on dev: a run of a scenario whose answers are the answer key's passes; one that leaves a
  table out, or other rows, fails on the check meant to catch it; nothing is written outside the
  run's folder.
