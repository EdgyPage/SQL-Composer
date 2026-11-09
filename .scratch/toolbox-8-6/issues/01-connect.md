# connect

Type: task
Status: open
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
