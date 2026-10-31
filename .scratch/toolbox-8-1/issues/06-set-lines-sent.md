# The write step sends the SET lines

Type: task
Status: resolved
Blocked by: 01
Size: S

## Question

A converted table's checklist asks the user to send the original's SET lines before its
write, with a call it prints (map, "What stops blocking": Q6).

## Done when

- `run_tables` sends each table's Session settings, its `session_settings()`, through
  `execute`, before its write, and records it in `sent.csv`; a table with none sends nothing
  more.
- The checklist and the Decisions have no SET-lines box.
- Its journeys show it (`tests/test_workflow_journeys.py`, ticket 01): the long-script journey's
  SET lines reach the Warehouse with no step of its own.

## Answer

Built 2026-10-31, before 02, since dropping the SET-lines box safely needs it.

- `project.run_tables` sends each table's own Session settings, its logic's
  `session_settings()`, through `execute`, before that table's first write, after the
  "dynamic_partitions" setting it already sent. A table whose logic defines none sends
  nothing more. Settled while building: a SET is not a row of `sent.csv`, which lists the
  sends that change a table, for the done-checks; the Done when's "records it in sent.csv"
  was wrong. The sending loop is `_send_in_order`,
  `_send_session_settings` the settings.
- A converted table's checklist has no SET-lines box, and its write()'s docstring says
  run_tables sends them.
- The journeys' "run each table's SET lines through execute" left the known-fiddling list:
  9 hand edits.
- Test: `tests/test_batches.py::test_run_tables_sends_a_tables_set_lines_before_its_write`.

### After the review (2026-10-31)

- Each table's logic is loaded once: `run_tables` gathers its writes and its
  `session_settings()` in one pass (`_writes_of` takes the logic).
- The settings are sent inside the same `try` as the write, so a failing send prints the
  "failed" line; after the Python-step check, so a table passed over sends none; and again
  whenever the write before was another table's, so another table's SET lines never hold for
  it.
- The dry run prints a table's settings before its writes, as they would be sent.
- Stale words fixed: how-to 9's prose, `session_settings()`'s own docstring, and the
  `${...}` finding now say run_tables sends them.
- Tests added: no SET lines sent for a table whose original had none; the dry run's order.

- Beginner reader: [06-beginner-reader.md](../reports/06-beginner-reader.md), each stop answered there.
