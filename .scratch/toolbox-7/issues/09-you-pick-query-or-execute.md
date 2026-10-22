# You pick query or execute: run_query and run_execute replace run

Type: task
Status: resolved
Blocked by: 08
Size: L

## Question

The user (2026-10-22), after 02 was built: "I don't want the toolbox to decide whether to use
the Execute or Query feature. I just want two function wrappers I define the internals of with
my own api. Decision logic inside the wrapper is too complex for this project." Grilled the same
day; the user said yes to all six answers below. ADR 0012, amended, records it.

1. `run(s, query=..., execute=...)` goes. `run_query(s, query)` gives back the DataFrame;
   `run_execute(s, execute)` gives back nothing. They keep what `run` added: the DataFrame
   check, the row Load limit, the Admin log, and explain(s)'s plan as text.
2. Each refuses the plain mix-up: a write, CREATE, Session settings or an Admin statement handed
   to `run_query`, a read or explain(s) handed to `run_execute`, saying which to call. Neither
   sends a Statement to the other call.
3. `unchecked_hive(text)` loses `returns_rows=`: an Unchecked statement goes through whichever
   the user calls.
4. Toolbox functions that need the warehouse take only the call they use, and none chooses:
   check_key, check_table_reference, write_table_reference, add_references and
   admin.add_columns take `query=`; `project.run_tables` takes only `execute=`, and everything a
   `write()` gives must be something that writes.
5. `admin.move_to_own_folder` gives only steps for `execute`. The count comparison becomes
   `admin.check_the_copy(t, query=query)`, called between the copy and the drop.
6. ADR 0012 amended; this ticket in the 7.0 map before any export. Then (2026-10-22): "Make
   sure this is version 7.1": 09 to 11 are Toolbox 7.1, and 7.0 stays as it was.

## Done when

- `run_query(s, query)` and `run_execute(s, execute)` are public, typed
  `Callable[[str], pd.DataFrame]` and `Callable[[str], None]`; `run` is gone. Each takes its
  call by position or as `query=` / `execute=`; `send=` is the Toolbox's refusal, as now, and
  the other call's name (`run_query(s, execute=...)`) is a refusal naming the right function.
- `run_query` takes a read, explain(s) and an Unchecked statement; `run_execute` takes a write,
  create_table, the upkeep Statements, the Admin statements, hive_settings(...) (one call per
  SET line) and an Unchecked statement. A Python step is refused by both, as now.
- `unchecked_hive(text)` takes no `returns_rows=`; the rows `run_query` gets for one are checked
  as a read's are.
- `admin.move_to_own_folder` gives the create and copy steps, and `admin.check_the_copy(t,
  query=query)` compares the counts and, once they match, gives the steps that finish the move
  (keep the files, drop, rename), so the drop can't be sent before the comparison. Both are
  logged in the Admin log as the steps were.
- `project.run_tables(*, execute=None, tables=None)`: the dry run with no `execute`; a read in a
  `write()` is refused, naming the notebook.
- Converted: every how-to, Worked example, test, tool, Template, admin notebook, Example
  project, the README template and the docstrings.
- CONTEXT.md: any entry naming `run` or `returns_rows` says `run_query` / `run_execute`.
- The version is 7.1 wherever the current version is named, and CHANGES.md has a `## 7.1` with
  "To update from 7.0"; its `## 7.0` stays as 7.0 was.
- CLAUDE.md's Definition of done, the beginner reader included.

## Answer

Built 2026-10-22 on dev as Toolbox 7.1 (03e0075, with ticket 10; drift fixes 2f27ee6; review
fixes efcb9d6).

- `run_query(s, query)` and `run_execute(s, execute)` replace `run`. Each refuses the plain
  mix-up, naming the other (`kinds.SENT_BY` decides which call a kind goes through); the other
  call's keyword (`run_query(s, execute=...)`); and, from the beginner read, your other
  function given in its place, known by its `__name__` (`run_query(s, execute)`), before
  anything is sent.
- `unchecked_hive(text)`: `returns_rows=` is refused, saying to pick the call.
- `run_tables(*, execute=None, tables=None)`: `query=` is refused; a read in a `write()` is
  refused before anything is sent.
- `admin.move_to_own_folder` gives the create and copy steps; `admin.check_the_copy(t,
  query=query)` sends the comparison through query, logged, and only then gives keep-files,
  drop and rename. That it gives the steps, not only checks, was this build's call, so a loop
  over the move's steps can't drop the old table unchecked; the user had agreed to "the count
  check becomes its own call".
- Version 7.1 in every Toolbox file, CONTEXT.md and the docstring; CHANGES.md `## 7.1` with
  "To update from 7.0", `## 7.0` as 7.0 was. ADR 0012 amended. CLAUDE.md names 7.1.

## Reviews

- Spec (2026-10-22): the row Load limit isn't applied to an Unchecked statement's rows, now
  said in a comment (no LIMIT is added to hand-written text); move_to_own_folder's docstring
  overstated the guarantee and miscounted (fixed); `returns_rows=` gave Python's TypeError
  (now refused). `to_hive`'s `_admin_hive` test reads data, not a kind: answered.
- Standards (2026-10-22): no breach. Fixed: wrapping; `kinds.is_a_query` for the repeated
  read-or-write test; `kinds.reads_rows` dropped, `kinds.sent_by` used by `_need_its_call`,
  whose parameter is `through`; `names_of_run` is `names_of_senders`; `_numbered`'s marking
  explained (the create step is create_table's). Answered: `check_the_copy` keeps the name
  the user agreed to, its docstring saying it gives the last steps; a Statement's `_kind`
  beside `_write`/`_ddl` is ticket 10's design, every maker setting both.
- Beginner reader (2026-10-22), costliest stops and what changed: a swapped function wasn't
  refused (now refused by name); the move's at-work loop lacked the Session setting, and its
  first line said it gave the whole move (both fixed); the Admin log's place outside a Project
  went unsaid (run_execute's docstring says it). Also fixed: `run_tables(query=)` and
  `returns_rows=` refused with a reason; "one SET line a call"; run_tables' "Statements that
  write"; how-to 22 says where `WITH old_counts` comes from; run_query names
  repair_partitions and compute_statistics instead of "upkeep", and "no INSERT_OVERWRITE or
  INSERT_INTO" instead of "no write"; the broken wrapping. Left: `run(...)` from 7.0 is
  Python's NameError (a star import can't refuse a name it doesn't bring; CHANGES.md 7.1 says
  what replaces it); `query=` by name or not on run_query/run_execute but by name elsewhere
  (CHANGES.md says so; the two calls take their call second, as their names say).
- Drift: 03e0075 opened D250 to D252, closed by 2f27ee6.
