# Python steps

Type: task
Status: resolved
Blocked by: 07
Size: M

## Question

The user (2026-10-21): "I want to be sure the lineage trace captures transforms done by python.
I don't want to model exactly what the equation is doing, but I do want to capture where the
function lives so I could inspect it myself." Then: "This is not an important feature. If this
is severely out of scope, push back." The pushback: nothing today writes a DataFrame back into
the warehouse, and making the Toolbox do so is the expensive part. They took the declare-only
version, as 7.0's last ticket and the first cut if 7.0 runs long.

## Done when

- `python_step(function, reads=[...], writes=table)` gives back a `PythonStep`, the name a type
  hint uses. `reads` holds Columns, or Tables for every column; `writes` is a Table. It sends
  nothing, and the Toolbox never moves its data.
- Where the function lives is read from the function itself: its file relative to the Project,
  its name and its first line. A function defined in a notebook cell names the notebook. A
  lambda, or anything that isn't a named function, is refused, saying why.
- A Table notebook's `write()` may list Python steps beside its Statements. `run_tables` passes
  over them, and `export_lineage` draws each one as one opaque box, "changed in Python by
  `building_blocks/margins.py:add_margin`, line 12", from the columns it read to the table it
  wrote. Each one also gets a section of the report, as an Unchecked statement does.
- An Intermediate how-to shows one: pull rows with a Statement, change them in pandas, save them
  with the user's own call (shown, not run), and declare the step.
- CONTEXT.md, in the words grilled on 2026-10-21. A new entry, **Python step**: "A change the
  user makes to data in Python, outside any Statement, and saves to a table themselves, declared
  to the Toolbox with the columns it read and the table it wrote. Lineage shows it as one opaque
  step naming the function that made the change and where it lives; the Toolbox never moves its
  data." Its _Avoid_ is `transform, pandas step, UDF`.
- CLAUDE.md's Definition of done, the beginner reader included.

## Answer

Built 2026-10-21 in a worktree (d4f7cee), merged into dev as ca21ba9; review fixes 44b5ecf and
d36be8d.

- `python_step(function, *, reads=[...], writes=table)` gives a `PythonStep` (new file
  sqlglot_composer/python_steps.py; public names 101). It sends nothing: run and to_hive refuse
  it, show_hive prints comment lines saying what it is.
- Where it lives is read from the function, unwrapped from any decorator: its file from the
  Project's folder (or its folder and name outside one), its name and first line; a function in
  a notebook cell is named by its notebook when JupyterLab gives the name, else "in a
  notebook"; a Table notebook's logic cell names that notebook. A lambda (also under a
  decorator), a builtin or anything not written with def is refused.
- export_lineage draws one opaque box with a "Where it lives" section; run_tables orders and
  passes over a step. How-to 41, "Declare a change made in Python" (Intermediate 22 to 41).

## Reviews

- Spec (2026-10-21): a decorated lambda got through (fixed); co_firstlineno's comment (fixed);
  show_hive's comment lines and run's refusal kept as needed behaviour.
- Standards (2026-10-21): `_refuse_a_read` -> NoReturn (fixed); the helpers renamed `step_*`;
  the unused `_function` dropped; how-to 41's "Building block" heading reworded.
- Beginner reader (2026-10-21): a Python step inside a Table notebook and run_tables is never
  shown (ticket 07's how-tos); which columns `reads=` lists (docstring now says); the notebook
  name's source (docstring now says).
- Drift: ca21ba9 opened D232, closed by 44b5ecf; d36be8d under review.
