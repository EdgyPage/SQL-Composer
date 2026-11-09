# built.run

Type: task
Status: open
Blocked by: 04
Size: M

## Question

Running, apart from building: writes through execute, reads through query, results by name, a
failure the scheduler sees (Q8, Q10, Q11, Q15).

## Done when

- `built.run(query, execute)` sends each in the build's order: a write, Admin or Unchecked
  statement through `run_execute`, a SELECT through `run_query`, printing a line as each
  works, as `run_tables` does.
- A Python step's table is written: its rows built through `query`, saved through `execute`.
- It gives back `results`, each SELECT's DataFrame by its name; nothing saved to a file.
- The first that fails stops the rest and raises, so the notebook fails; before raising it
  prints `START_FROM = "<table>"` to rerun from it, and that every table before it was
  written.
- It writes no lineage and no file of its own; an Admin statement is logged by `run_execute`.
- Tests on the Example database: a run writing three tables and returning a SELECT; a failure
  halfway and its START_FROM rerun; a Python step.

## Answer
