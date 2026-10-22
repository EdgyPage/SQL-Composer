# The Toolbox reaches the warehouse through the user's query and execute

Status: accepted, built by Toolbox 7.0; amends ADR 0004, whose one way out, `send`, becomes these
two calls

Up to 6.1 the user's Project held one `send(hive) -> DataFrame`, and every Statement went through
it, writes and `SET` lines included, whose result the Toolbox never read. On 2026-10-21 the user
said their work's API has two calls, `execute`, which gives back no DataFrame, and `query`,
which does, and that one `send` left them reading the code to find what it expected.

So in 7.0:

- **The Project's `warehouse.py` holds `query(hive) -> DataFrame` and `execute(hive) -> None`**,
  where `send.py` was.
- **Each Toolbox function takes only the calls it uses**, as keyword arguments, so its signature
  says what it needs: `check_key(t, query=query)`, `run(s, query=query, execute=execute)`.
- **The Toolbox picks the call**: a read, DESCRIBE, SHOW and EXPLAIN go to `query`; a write,
  CREATE, MSCK, ANALYZE, a Session setting and an Admin statement go to `execute`. An Unchecked
  statement says which with `returns_rows=`, which has no default.
- **`send` is removed, not deprecated**: passing `send=` is refused, naming the new arguments.

## Considered options

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
- The Example database answers `query` as `send` did, and its `execute` prints the Hive and
  changes nothing, since it answers reads only.
- ADR 0004's policy is unchanged in substance: the Toolbox's only ways out are the user's own
  calls, now two of them.
