# A conversion's files name the right notebook and database

Type: task
Status: resolved
Blocked by: 04
Size: S

## Question

Found by round one:

- a table `new_table` made has a Table notebook header and a checklist.md that send its
  Decisions to convert.ipynb's decisions cell, not new_table's (W3-1, W3-2);
- batch.md lists a new_table or Excel query's table as `default.<name>` (W3-1, E3-2);
- scan.md says a bare SELECT has "its INSERT OVERWRITE" (E2-2).

## Done when

- Each file names the Workflow that made the table, its database as the Project's Dev
  Database, and a bare SELECT as a query, each held by a test.

## Answer

`_decisions_notebook(made_for)` names the Workflow's notebook, and the Table notebook's header,
checklist.md (written again, it keeps the notebook it named) and the batch's Next line all use
it. batch.md lists a table a query alone writes as `- <copy>, from its query: ...`. The scan
of a query's table says the query becomes the Saved table's write (`_as_a_querys`). Found on
the way: every scan counted the one-line Hive it is rewritten as, "1 line of Hive", its
findings all "line 1": it now counts the script's lines and drops the one line's number.
`tests/test_run_workflow.py::test_a_table_made_from_its_query_has_files_naming_new_table`
holds each. The drift review of c514bf5's D398 (two docstrings on done steps) is fixed here.

## Review

- Standards: the scan no longer changes the findings it is given (`_scan_lines` takes
  `query_alone` and words a query's write as `_as_a_querys_write` lists it), matched on
  `converting.WRITE_FINDING`; the notebook header's wording is an `if`; `notebook` and
  `made_for` are required; batch.md's notes are built once; do_next's docstring is in plain
  sentences.
- Spec: the Dev Database is held by the test's `- mart_dev.failed_jobs, from its query:` line.
  A checklist a new_table table wrote before 8.2 names convert's notebook and keeps it when
  written again: ticket 07's Upgrade step has it to rewrite. A convert batch of bare SELECTs
  gets the same batch.md and scan wording, as the ticket's "a bare SELECT" asks.
