# warehouse.py takes a connection

Type: task
Status: resolved
Blocked by: -
Size: S

## Question

The user (2026-10-31): "adjust the warehouse to take in a connection, not an execution or
query. take in a variable conn and conn.execute(sql) and conn.query(sql) are on the inside.
query returns a df, execute returns nothing." Asked how the Toolbox reaches `conn`: "I would
like to pass the connection once and have the connection methods be wrapped in the query and
execute."

## Done when

- The warehouse.py `project.start()` writes holds `conn`, the user's connection, set once, and
  `query` and `execute` that pass each Hive string to `conn.query` (a DataFrame back) and
  `conn.execute` (nothing back). Until the user sets it, `conn` is the Example database.
- Every Toolbox call still takes `query` and `execute`, as before: nothing else changes.
- `start()`'s report, its docstring, how-to 01, the README template, Copilot file 01, the
  starter Example project's README and CHANGES.md's 8.0 say to set `conn`.
- A Project's own warehouse.py is the user's; the 8.0 Upgrade (ticket 20) leaves it as it is.

## Answer

Built 2026-10-31.

- `WAREHOUSE_TEXT` holds `conn = example_database`, with a comment saying to set it to the
  user's connection; `query(hive)` returns `conn.query(hive)` and `execute(hive)` calls
  `conn.execute(hive)`. The Example database's module has both, so it serves as the default.
- `start()` ends "Next: set conn, your connection, in warehouse.py.", and its completed
  report and the pre-7.0 note say the same. Every doctest and how-to that shows it follows.
- How-to 01's "Read the warehouse.py start wrote" shows the new file, and "Set your
  connection" (in place of "Write your query and execute") says to set `conn`, and how to
  change `query` when a connection gives rows as dicts or through a cursor.
- The README template, Copilot file 01 (and the all-in-one file), both Example projects'
  warehouse.py and the starter's README are regenerated or rewritten to match.
- The snapshot is written again on purpose: start's report changed in every test that starts
  a Project.

Reviews:
- **Drift, D311 to D314.**
  - D311: start()'s pre-7.0 line points to CHANGES.md's 8.0, which now says what to do with
    send.py.
  - D312: how-to 01's Goal and Common mistakes, and how-to 06, speak of the connection.
  - D313: the README's file table names `conn`.
  - D314: CONTEXT.md's Warehouse says both calls pass the Hive to `conn`.
- **Beginner reader (opus)**, taken:
  - `execute` with a cursor is shown beside `query`;
  - whether one session is the connection's or the user's to keep;
  - that `conn` can be any object with the two calls, and that `my_api` is a made-up name;
  - what the DataFrame's columns are named;
  - that `execute` drops what `conn.execute` gives back;
  - that `query` in the page is always the function in warehouse.py;
  - that a 7.x warehouse.py keeps working.

  Not taken: the printed warehouse.py wrapping a docstring line in how-to 01. The page
  wraps long output lines, and the doctest reads them as one.
