# The loop's harness: agents, relay, workspace, scoring

Type: task
Status: resolved
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

## Answer

Built 2026-11-01.

- `tools/usability_loop.py`: `prepare`, `route`, `answer`, `score [--record]`. A run's folder
  is made outside the repo (`<temp>/usability-loop/runs/<name>/`), and its agents run a Python
  made outside it too (`docs/usability-loop.md`, "Once"), so nothing of dev's, the answer keys
  most, sits near their work. It holds `main/` (the Clean tree, built from dev's last commit by
  the export's own `committed_files` and `build`), `from_your_team/`, `my_work/`,
  `team_connection.py` and `run_notebook.py`, and `_loop/`, the loop's own.
- No Project is built for them: starting one is the README's first step, part of what's
  measured. `team_connection.py` is the team's connection a user is given, to a warehouse that
  keeps each table between processes, `SavedWarehouse` in `tools/workflow_warehouse.py`.
- `tools/notebook_runner.py`, copied in as `run_notebook.py`, runs a notebook's cells as Run All
  does; its `exec` is an `ALLOWED` site, the user's OK given ("A cell runner").
- Each phase's message gives its role what that person has: a technical user and a converter
  get Python, the connection and the runner; a non-technical user only openpyxl, as their hands
  on Excel. Everyone keeps what they make in `my_work/`.
- A question goes to Copilot as one chat: file 00 pasted, the question, Copilot naming a file;
  then that file pasted in the same chat, and any file the user attaches, a workbook shown as
  Copilot reads one (`workbook_text`); each message and reply kept in `_loop/`. At most five.
- `score` compares each table the key holds, columns by name and rows in any order, values by
  kind (text never read as a number, NULL and NaN alike), fails a table with other columns,
  and checks each file the key holds, and the text it must hold. Excel scenarios' keys are
  computed from the workbook's own values (ticket 03), so scoring against the key is scoring
  against the workbook.
- `--record` copies the run, but for `main/`, into `.scratch/usability-loop/runs/` and adds a
  row to `.scratch/usability-loop/results.md`.
- `.claude/agents/zero-context-user.md`, on Haiku; the Copilot stand-in is `copilot-proxy`.
- Tests: `tests/test_usability_loop.py`, 15: the warehouse kept between processes; the runner;
  a run holding what the user has and nothing of the key, nothing written outside it; each
  role's message; the key's end passes; a missing table, other rows, numbers as text, an extra
  column and a file without its text each fail on their check; too many questions; one chat
  per question; a workbook attached; main's tree built from dev.
- Code review: Standards: names made verbs or what they return, `counted` and `in_words`,
  one message-writer for both hops, `RunScore.passed` a property, a nested comprehension
  unrolled; the loop's words (scenario, run, round) are dev's tooling, not the Toolbox's
  domain, as the Copilot eval's are. Spec: the runs were inside the repo and their Python dev's
  (now both outside); the second hop didn't carry file 00 or the first exchange, nor an
  attachment (now it does); text could pass as a number and an extra column was ignored, and a
  file's text wasn't checked (all fixed); replies weren't kept (now each has its file); the
  non-technical role was given Python's runner (now only openpyxl); no message said where work
  goes (`my_work/`).
