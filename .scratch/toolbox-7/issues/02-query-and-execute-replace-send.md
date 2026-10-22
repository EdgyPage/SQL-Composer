# query and execute replace send

Type: task
Status: resolved
Blocked by: 01
Size: M

## Question

The user (2026-10-21): "There are two ways my work uses API functions on its databases. Execute
and Query. Execute does not return a dataframe, query does. Currently we only have space for one
api point in send.py." Asked to choose, they chose: "deprecate Send in favor of Execute and
Query so I don't get confused", with no wrapper object ("what is the value of a wrapper when I
can just use the two functions directly?"). The map's "The warehouse calls" and ADR 0012 hold
the design.

What exists (2026-10-21): `send` is always passed in, never imported by the Toolbox. `run`
(`running.py:638`) already checks for a DataFrame only from a plain read (`running.py:684`);
writes and DDL pass back whatever `send` gave, unchecked. `tables._ask` (`tables.py:1166`) reads
DESCRIBE and SHOW PARTITIONS; one Admin check reads a result (`_counts_match`, `admin.py:641`).
`example_database.send` answers reads only and refuses the rest.

## Done when

- A Project holds `warehouse.py`, with `query(hive: str) -> pd.DataFrame` and
  `execute(hive: str) -> None`, where `send.py` was; `project.start()` writes it, and the
  Templates and admin notebooks import `from warehouse import query, execute`. It imports none
  of the user's files and stays Level 0.
- Every Toolbox function that took `send=` takes `query=`, `execute=` or both, only the ones it
  uses: `run`, `check_key`, `check_table_reference`, `write_table_reference`,
  `project.add_references`, `project.run_tables`, `admin.add_columns`,
  `admin.move_to_own_folder`, and any other the grep finds. Each signature's type hints say
  `Callable[[str], pd.DataFrame]` or `Callable[[str], None]`.
- `run` sends a read, DESCRIBE, SHOW and EXPLAIN to `query`, and refuses what isn't a DataFrame
  as now; it sends a write, CREATE, MSCK, ANALYZE, a Session setting and an Admin statement to
  `execute`, and never reads what that gives. An Admin check that needs rows reads them with
  `query`. A step whose call wasn't passed is refused, naming the argument.
- `unchecked_hive(text, returns_rows=...)` needs `returns_rows`, with no default, and `run` sends
  the text to the call it names.
- `example_database.query` answers as `send` did; `example_database.execute` prints the Hive's
  first line and changes nothing. `example_database.send` is gone.
- `send=` passed to any Toolbox function is the Toolbox's refusal, naming `query=` and
  `execute=`; `project.check()` reports a `send.py` with no `warehouse.py`, saying how to make it.
- The offline policy's and code audit's notes, and ADR 0004's readers, say `query` and
  `execute` where they said `send`.
- The how-tos, Worked examples, Example projects and README still run, changed only as far as
  the new names need; 07 rewrites them.
- CHANGES.md's "To update from 6.x": rename `send.py` to `warehouse.py` and split it in two, as
  shown, and change each `send=send` to the calls the function takes.
- CONTEXT.md, in the words grilled on 2026-10-21:
  - **Warehouse** adds: "The Toolbox reaches it only through the user's two calls: `query`,
    which gives back rows as a DataFrame, and `execute`, which gives back nothing, as the user's
    own API does." Its _Avoid_ adds `send`.
  - **Level**: "the Table references and the warehouse calls are Level 0".
  - **How-to**: "such as your own query and execute".
- CLAUDE.md's Definition of done, the beginner reader included: `send`'s contract was where the
  user stopped and read the code.

## Answer

Built 2026-10-21 on dev (c898236; reviews' fixes 7f37816).

- A Project holds `warehouse.py` with `query(hive) -> pd.DataFrame` and `execute(hive) -> None`;
  `project.start()` writes it and refuses a folder holding it or a `send.py`; `project.check()`
  reports a `send.py` with no `warehouse.py`. Its docstring and how-to 01 say both calls raise
  when the warehouse fails, and share one session.
- `run(s, *, query=None, execute=None)` picks the call: a read and explain(s) go to `query`; a
  write, create_table, the upkeep Statements, Session settings and the Admin statements to
  `execute` (run gives back None), but for `admin.move_to_own_folder`'s count step, which reads
  through `query`. A step whose call wasn't passed is refused, naming it.
- `unchecked_hive(text, *, returns_rows: bool)`, no default; returns_rows=True's rows are
  checked as a read's are.
- `query=` (keyword only) on check_key, check_table_reference, write_table_reference,
  project.add_references, admin.add_columns and admin.move_to_own_folder; run_tables takes
  both, and is the dry run with no `execute`. Each takes `**removed`, so `send=` is the
  Toolbox's refusal naming what to pass, and any other unknown keyword a refusal too. `query`
  defaults to None where it is needed, so a 6.x call with `send=` meets that refusal before
  Python's missing-argument TypeError; a missing `query` is refused by `need_warehouse_call`.
- `example_database.query` answers SELECT, DESCRIBE and SHOW PARTITIONS; `example_database.execute`
  prints the Hive's first line and changes nothing; `example_database.send` is gone.
- Converted: every how-to, Worked example, test, tool, Template, admin notebook, Example
  project, the README template, the offline audit, the offline hook's text and CLAUDE.md.
  New tests cover the routing, the refusals, returns_rows, start() and check().
- CHANGES.md `## 7.0` "To update from 6.x": warehouse.py, each `send=`, returns_rows=, the
  Example database. CONTEXT.md: Warehouse, Level and How-to as the ticket says.

## Reviews

- Spec (2026-10-21): nothing missing. Answered: the refusal of any unknown keyword, the bool
  check on returns_rows, and execute's refusal of non-text are the Toolbox's usual checks; the
  README's warehouse.py block is what its step needs to stay true; ADR 0004's body stays as
  history, its Status pointing to 0012; run_tables with only `query` is the dry run, as its
  report says ("Pass execute= to run them").
- Standards (2026-10-21): no breach. Fixed: the long lines this ticket added, and
  check_table_reference's "never refuses anything". Answered: `query=None` and `**removed` stay,
  since without them a 6.x `send=` call meets Python's TypeError instead of the Toolbox's
  refusal; run's branches stay plain, one per kind of step, as the standards prefer.
- Beginner reader (2026-10-21), costliest stops and what changed: nothing said the two calls
  must raise on a failure (now how-to 01, warehouse.py and CHANGES say so); CHANGES said every
  Admin statement goes to execute (now names the move's count step, and so do run's and the
  admin module's docstrings: drift D223, D224); example_database.query claimed EXPLAIN and its
  refusal sent a SHOW to execute (now it says which reads it answers, and tells a read from a
  write). Also fixed: "a query" for the user's function now says `query` function; the session
  sentence; the not-a-function refusal names the kind instead of printing the value; run's
  return line; unchecked_hive's "can't tell"; CHANGES's "but SET". Left: the Callable paragraph
  in how-to 01 (ticket 07 rewrites the how-tos), `run(s, query)` positional stays Python's
  TypeError (CHANGES says so), and "Opt-out: none" is the house format.
- Drift: c898236 opened D223 and D224, closed by 7f37816.
