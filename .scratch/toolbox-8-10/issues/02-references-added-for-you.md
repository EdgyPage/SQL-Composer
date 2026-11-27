# Table references added for you

Type: task
Status: open
Blocked by: -
Size: M

## Question

Three places refuse when a table they read has no Table reference and send the user to the
references Workflow first. Make each add it, as convert does (round 1, Q6; the map's "Table
references in the Workflows" note). The user: "I want every step to be automatic if it's
supported and expected behavior."

## Done when

- **`new_table` with QUERIES**, **`project.new_run_value(latest_partition=...)`** and **the
  sources Decision** (`write_decisions`) each add the missing reference themselves, the way
  convert's `_write_missing_references` does: a DESCRIBE through the user's `query`, the Key
  proposed and left a proposal to accept, the Reference sheet rebuilt.
- **Each says what it added**, one line per reference, naming its file.
- **A DESCRIBE that fails** refuses as today, naming the table and giving the warehouse's error,
  and nothing is written for it.
- Promote and schedule are unchanged: promote reads only dev tables, and schedule reads no
  outside table.
- **Tests**: each of the three adds a reference and goes on, on the Example database; each says
  what it added; a failed DESCRIBE refuses naming the table. The refusals these three gave are
  gone from `tests/snapshot/known.txt`, and their how-tos and Copilot files no longer tell the
  user to add the reference first.
- The beginner reader runs, since refusal messages change.
