# run_tables refuses what write_day gives

Type: task
Status: resolved
Blocked by: -
Size: S

## Question

Found while hinting ticket 02: `project.run_tables` passes what each table's `write_day(day)`
gives straight to `lineage.in_order`, unchecked. A `write_day` that gives Session settings,
or anything but Statements and Unchecked statements, stops with Python's AttributeError, not a
four-part message. Confirm it, then refuse it as the Toolbox refuses a wrong value elsewhere.

## Done when

- A `write_day` giving something `run_tables` can't send is refused with the four-part message,
  naming the table and what it gave; a test holds it.
- The pytest run passes, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).

## Answer

Built 2026-10-21 on dev, test first; the user asked for it in 6.1.

- `project._writes_of` loads a Table notebook's logic, calls its `write_day(day)` and checks
  each write it gives before `run_tables` puts any in order or sends any. A Statement (an
  Admin statement among them), an Unchecked statement or a list or tuple of them passes;
  anything else, an empty list included, is refused with a TypeError naming the call, the
  table and what write_day gave, by `_refuse_a_write`.
- The refusal's fix names the likely causes: a lost `return` (None), Hive written by hand
  (`unchecked_hive(...)`), and Session settings, to send before run_tables, which hold only
  while the send keeps one session.
- `tests/test_project.py` holds six cases: Session settings, a string, None, a list holding
  Session settings, a tuple, an empty list. Each failed first with an AttributeError (the empty
  list passed, then failed at `max()` with a send).
- run_tables' docstring says what write_day may give; CHANGES.md's 6.1 says it is refused.

## Reviews

- Beginner reader (2026-10-21, with 08): fixed, the refusal says to send Session settings
  before run_tables and names a lost return; the docstring counts an Admin statement as a
  Statement; "can't send" became "can't put in order" in CHANGES.md. Left: the Session
  settings' repr names show_hive inside the message.
- Spec (2026-10-21, with 08): fixed, an empty list is refused (it slipped through), a tuple is
  called a tuple, not a list.
- Standards (2026-10-21, with 08): fixed, "which isn't a Statement or an Unchecked statement";
  the why says "the tables each Statement reads and writes"; the fix names unchecked_hive; a
  named `several` flag replaced `writes is written`; the docstring rewrapped. The check moved
  to `_writes_of` so run_tables stays under ruff's complexity limit.
