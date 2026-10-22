# query and execute replace send

Type: task
Status: claimed
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
