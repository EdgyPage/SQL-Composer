# A journey through Script tags, and the hand edits it needs today

Type: task
Status: resolved
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
Built 2026-11-04.

- **The journey**, `test_convert_a_script_with_script_tags` in
  `tests/journeys/test_workflow_journeys.py`: `TAGGED_STATEMENTS` pairs each statement with the
  dev table its tags are a Decision of, and `TAG_VALUES` says what each tag stands for there,
  so the originals are written by the script with each tag filled in (`_filled_in_script`), as
  the program the user copies from fills them. It holds a bare `PERIOD_END` twice in
  daily_close, a quoted `PERIOD_END` standing for another date in monthly_fails, a bare
  `MinMins` in a staging table folded into monthly_fails, and a quoted `skip_team_2`. It is
  written as it runs once 03 lands: the tags answered under `"tags"` in the decisions cell, the
  end goal each table compared and holding its original's rows.
- **Today** it is `xfail(strict=True)`, failing at the user's snag: right after step 1, "no
  Table folder for mart_dev.daily_close_mart", the bare-tag table left an Unchecked statement.
- **KNOWN_FIDDLING stays `()` for convert.** No hand edit inside the Project gets this batch to
  its end goal today: the bare-tag statement never becomes a Table folder to fix, so the only
  way through is rewriting the script itself before convert, which is the user's snag, not a
  step. Once 03 lands, the journey makes none.
- **What the batch reader does today**, `tests/test_script_tags.py`: a bare tag, in an INSERT,
  in a staging CREATE ... AS, or twice, leaves its statement OTHER, naming no table, reading
  nothing, its note sqlglot's; a quoted one reads as a string, the tag kept in it. 02 changes
  these.
- **Code review:** Standards: a helper named `_read` that reads no file (now
  `_statement_of`), and the journey's comment made two plain sentences. Spec: the xfail now
  fails at step 1's missing Table folder, not later; unit tests added for the staging and
  twice shapes. Left, settled: no `_through_the_runner` twin yet, since a runner journey adds
  nothing while the plain one can't pass; 03 adds it with the tags answered.
