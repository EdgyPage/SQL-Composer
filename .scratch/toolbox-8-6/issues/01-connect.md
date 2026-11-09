# connect

Type: task
Status: resolved
Blocked by: none
Size: M

## Question

warehouse.py takes a connection, sets it as the one it uses, and fails when none is set (map,
"connect").

## Done when

- `project.WAREHOUSE_TEXT` writes `connect(connection)`, which sets the module's connection,
  and `query`/`execute` calling its `query(hive)`/`execute(hive)`. Before `connect`, each
  refuses with the four parts: "No connection: call connect(...) first", the why (each
  notebook runs on its own, so each connects at its top), and the fix naming the setup cell.
- `connect` refuses a connection with no `query` or no `execute`, naming the one missing.
- Each Toolbox-written notebook's setup cell imports `connect` and has a `connect(...)` line:
  `example_database` in the Example projects, a line to fill in a new Project's (with the
  comment on a connection kept in a file outside the Project, as today's warehouse.py has).
- The how-tos, Worked examples, journeys, the Workflow runner's notebooks and `run_tables`'
  notebook connect first; nothing in the Toolbox reads `conn` any more.
- A journey: a notebook run without its `connect` line gives the refusal, not a traceback from
  `None`.
- `project.start()`'s "Next:" line names connect, not conn.

## Answer

Built 2026-11-09.

- `project.WAREHOUSE_TEXT` writes `connect(connection)`, `query(hive)` and `execute(hive)`
  over one module-level `_connection`, None until a notebook connects; `connect` again
  replaces it. `connect` refuses (TypeError) an object whose `query` or `execute` isn't
  callable, naming the first missing and the object's type; `query` and `execute` before it
  refuse (RuntimeError) with "No connection: call connect(...) first. query(...) was called
  before this notebook gave warehouse.py its connection.", the why (each notebook runs on its
  own, in a Python of its own) and the fix naming the setup cell's `connect(...)` line.
- **Decided: warehouse.py imports nothing of the Toolbox, so writes its four parts itself.**
  Code a user reads imports only public names, and `refusals.refuse` isn't one; a
  `_refuse` of four lines in warehouse.py writes the message `refuse` writes, which
  `tests/test_connect.py` holds to the Toolbox's `_four_part_message`. warehouse.py imports
  only `typing` and `pandas`.
- **Decided: the line to fill in is a comment, `# connect(your_connection)`**
  (`project_templates.CONNECT_PLACEHOLDER`), under a comment saying what to write and how a
  connection in a file outside the Project is imported (`CONNECT_LINES`). Not a `<...>`
  placeholder: a Workflow notebook's file-only steps still run before it is filled in, and
  the first call to the warehouse gives the refusal.
- **Decided: "every Toolbox notebook" is every notebook that imports from warehouse**: each
  Workflow notebook (`WORKFLOW_PATH_LINES`), `check_references` (its cell under the path),
  `run_tables` (a new cell under the path, since a Run value reading the warehouse needs it
  even for the printing run), each Table notebook Template's cell 1 (and its "The code cells"
  line), and a converted table's notebook. check_project, new_block, remove and
  refresh_reference_sheet reach no warehouse and are unchanged.
- **Decided: the Example projects fill the line as a user would**, in
  `tools/example_project.py`'s `_connect_each_notebook`: `from sqlglot_composer import
  example_database` and `connect(example_database)` in each notebook. Their Templates stay as
  start() writes them: filled in, an Upgrade's Template steps read them as changed by the user
  and mark them (how-to 28 showed it). Their sources' Table notebooks hold the Template's
  cell 1.
- `project.start()`'s report ends "Next: at the top of each notebook, fill in connect(...)
  with your connection."; every docstring quoting it, how-to, the README and
  `tools/workflow_graph.py` with it. Run again in a Project lacking warehouse.py, it says
  "each notebook gives its connect(...) your connection"; for one from before 7.0, it points
  at CHANGES.md's 8.6.
- How-tos 02 to 27 connect with `connect(example_database)` under their warehouse import; how-to
  01's steps 7 to 9 are rewritten for connect (warehouse.py shown, the refusal shown, a
  cursor's `query` written over `_connection`); 06, 07 and 26 list cell 1 as the Template
  writes it; 29 (from `workflow_graph.py`) says to fill in the line. The README's step 5, its
  doctest and its file list say connect.
- Journeys: the `started` fixture fills each notebook's line with the stand-in imported from
  `journey_conn`, as `_set_conn` set conn once before, and counts no action for it.
  `test_a_notebook_run_without_its_connect_line_refuses`: the references notebook with its
  line unfilled stops at step 1, add_references reporting "DESCRIBE failed: RuntimeError: No
  connection: call connect(...) first. ...", by hand and through the runner, then goes on once
  filled in.
- **Decided: what only 8.6's Upgrade step can make pass is xfail(strict) until ticket 12**:
  the two upgrade journeys (`UNTIL_TO_8_6`, ImportError: an 8.4 Project upgraded today gets
  8.6's Workflow notebooks, which import `connect` from a warehouse.py without it; their
  fixture skips its hand-edit check while so marked), and
  `test_the_example_projects_of_each_version_since_8_3_upgrade_straight_into_this_ones`
  (no step connects the notebooks yet). Ticket 12 removes each mark. `tests/test_upgrades.py`'s
  8.2 test now checks the warehouse.py it writes has `connect`, and its notebook-mark test
  that run_tables' cell 3 is the new connecting cell.
- Usability loop: `connect_the_team(root)` fills each notebook's and Template's line (the
  placeholder, or an Example project's `connect(example_database)`) with team_connection.py's
  `conn`, and still sets an older warehouse.py's `conn` line; `reference_end` connects
  warehouse.py to the run's warehouse when it has `connect`. Copilot file 01's warehouse.py
  bullet says connect (shortened to stay under 8,000 characters); `connect` is one of the
  user's own calls in `tests/test_copilot_files.py`, and `_check_connected` and `_connection`
  names how-to 01 may use in `tests/test_how_tos.py`.
- Tests: `tests/test_connect.py`; `tests/test_usability_loop.py`; the journey above. The whole
  suite passes (exit 0), its snapshot written again.
- Not run here: the `code-review` skill and the beginner reader (a refusal, how-to 01, the
  README and the Templates changed), both for the caller.
- Left for ticket 10: CHANGES.md's 8.6 (and how a Project from before 7.0 writes warehouse.py,
  which start() now points at); how-to 01 and the README read again as a whole; Copilot files
  01's imports line, `_always.txt` and any example naming the two calls; `docs/workflows.md`;
  `tools/copilot_eval.py`'s stand-in warehouse.py, still conn-shaped, once Copilot files teach
  connect. Left for ticket 12: warehouse.py and the notebooks of a Project upgraded from 8.5.
