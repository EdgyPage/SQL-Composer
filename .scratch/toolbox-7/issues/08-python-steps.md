# Python steps

Type: task
Status: open
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
