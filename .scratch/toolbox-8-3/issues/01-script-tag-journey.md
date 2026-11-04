# A journey through Script tags, and the hand edits it needs today

Type: task
Status: open
Blocked by: -
Size: M

## Question

Before anything changes, run the user's snag as a user runs it: the convert notebook, top to
bottom, on scripts holding Script tags (map, "What a Script tag does to a Conversion today").

## Done when

- `tests/journeys/test_workflow_journeys.py` gains a convert journey on a batch of scripts, run
  as the other journeys are (the notebook the Project ships, the Example database's `query` and
  `execute`), whose scripts hold:
  - a bare tag, `WHERE ... <= <PARM="PERIOD_END"/>`, in one table's INSERT;
  - a quoted tag, `'<PARM="PERIOD_END"/>'`, in a second table's, standing for a different date;
  - a tag in a staging table folded into a table that reads it;
  - the same tag twice in one table;
  - tags with other names besides `PERIOD_END`, such as `<PARM="RunMonth"/>` and
    `<PARM="SRC_LIMIT_2"/>`: any variable name is a tag, `PERIOD_END` only an example.
- It ends on the convert Workflow's end goal: each table written in dev and compared with its
  original, the Batch finished. Each original is written first by the scripts with each tag
  filled in as the program the user copies from would.
- Every hand edit it needs today is a named step in `KNOWN_FIDDLING`: a file opened and fixed,
  a cell the user makes. Today the bare-tag table is an Unchecked statement, so the journey
  can't reach its end goal; it is marked expected to fail, naming why, until 03 lands.
- A unit test per tag shape holds what `batch_statements` does with it today, for 02 to change.

## Answer
