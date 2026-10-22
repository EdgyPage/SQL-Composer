# The Toolbox reaches the warehouse through the user's query and execute

Status: accepted, built by Toolbox 7.0; amends ADR 0004, whose one way out, `send`, becomes these
two calls. Amended 2026-10-22: the user picks the call, not the Toolbox

Up to 6.1 the user's Project held one `send(hive) -> DataFrame`, and every Statement went through
it, writes and `SET` lines included, whose result the Toolbox never read. On 2026-10-21 the user
said their work's API has two calls, `execute`, which gives back no DataFrame, and `query`,
which does, and that one `send` left them reading the code to find what it expected.

So in 7.0:

- **The Project's `warehouse.py` holds `query(hive) -> DataFrame` and `execute(hive) -> None`**,
  where `send.py` was.
- **Each Toolbox function takes only the calls it uses**, as keyword arguments, so its signature
  says what it needs: `check_key(t, query=query)`, `run_query(s, query)`.
- **The user picks the call** (amended 2026-10-22): `run_query(s, query)` sends a Statement
  through `query` and gives back its rows; `run_execute(s, execute)` sends one through
  `execute` and gives back nothing. Each refuses the plain mix-up, a read handed to
  `run_execute` or a write to `run_query`, saying which to call; it never sends a Statement to
  the other call. An Unchecked statement goes through whichever the user calls.
- **`send` is removed, not deprecated**: passing `send=` is refused, naming the new arguments.

## Considered options

- **The Toolbox picks the call**, `run(s, query=..., execute=...)` routing each kind of
  Statement, with `returns_rows=` on an Unchecked statement. Built by 7.0's ticket 02, then
  reversed by the user on 2026-10-22, before any export: "I don't want the toolbox to decide
  whether to use the Execute or Query feature. I just want two function wrappers I define the
  internals of with my own api. Decision logic inside the wrapper is too complex for this
  project." Which call a Statement goes through is now said where it is sent.

- **A `Warehouse` object holding both calls**, passed as one argument. Rejected by the user: it
  saves an argument at the cost of a type to learn, where the two functions say plainly what each
  Toolbox function needs.
- **One `send` with a mode argument.** Rejected: the user's API already has the two calls, and a
  mode is one more thing to get right on every call.
- **Keep `send` working beside them, with a warning, for a version.** Rejected: the user wanted
  one name for each thing, not two.

## Consequences

- Every Project's `send.py` is rewritten as `warehouse.py`, and each `send=send` becomes the
  calls that function takes; `project.check()` reports a Project still holding only `send.py`.
- `run` is gone: each `run(s, send=send)` becomes `run_query(s, query)` or
  `run_execute(s, execute)`. Toolbox functions that only read take only `query=`; `run_tables`,
  which only writes, takes only `execute=`. `admin.move_to_own_folder` gives only steps for
  `execute`, and `admin.check_the_copy` compares the counts through `query` between the copy and
  the drop.
- The Example database answers `query` as `send` did, and its `execute` prints the Hive and
  changes nothing, since it answers reads only.
- ADR 0004's policy is unchanged in substance: the Toolbox's only ways out are the user's own
  calls, now two of them.
