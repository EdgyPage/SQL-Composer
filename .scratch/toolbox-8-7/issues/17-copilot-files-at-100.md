# The Copilot files at 100

Type: task
Status: open
Blocked by: 16
Size: L

## Question

After ticket 16, the held-out rounds stand at 94 (files 01 to 17, T49 failing) and 50 (the
Metric request, M06 failing). The user (2026-11-13): "Add a few more varied tests to the M suite
to help shape performance. Redo the files and tests again. I want 100%s. If more files are
needed, then that's fine. I want searchable, indexable instructions that guide models to
correct patterns without having to think too hard."

## Done when

- **The Metric request suite grows,** in `tools/metric_eval_tasks.py`: new, varied tasks that
  cover what the six don't, such as a ratio, a running or period-over-period figure, a
  distinct count, a threshold or band, a first or latest per group, a quantity the tables
  can't give (the request must say so, not invent it), a muddled pair, and sample rows. Most
  are dev tasks, to shape the file; at least two more are held out, so the held-out score
  rests on more than two tasks. Each has its reference Hive, its naive Hive and its key's
  numbers, held by `tests/test_metric_eval.py`.
- **The files are written to be looked up, not reasoned through:** short numbered rules with
  ids, a "When the user says X, do Y" pattern table, worked patterns to copy, and a Self-check
  a model ticks off. A file may split into more files where one can't hold it, each at most
  9,000 characters, with file 00's list, the all-in-one file and the evaluations following.
- **Every evaluation scores 100 on haiku:** files 01 to 17 dev and held-out, the Excel
  evaluation dev and held-out, the Metric request dev and held-out. A dev round that misses is
  fixed in the files, by the general fault, never a task's answer. A held-out round is run
  once per files version; a miss there is fixed the same way and the held-out round run again
  on the new version, each recorded. The record says which held-out tasks shaped a fix.
- **100 holds twice:** the last files version's held-out rounds pass on two runs in a row.
- The suite passes; the code review and the beginner reader run; the drift review is clean.
