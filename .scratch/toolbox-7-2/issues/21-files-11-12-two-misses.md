# Files 11 and 12: the two held-out misses fixed, and held-out scored again

Type: task
Status: claimed
Blocked by: 20
Size: S

## Question

Ticket 20's held-out round left Haiku at 94%, one task short of 95%, with two causes written
up in `.scratch/copilot-eval/excel-files-11-12-misses.md`: a step written as a sql block of its
own (X69), and a loaded Table taken for a step when another query reads its query (X70). The
user (2026-10-29): "Fix and rerun".

As the fixes come from held-out failures, held-out X69 and X70 no longer count as unseen; new
tasks for both causes do.

## Done when

- New tasks for both causes, written and committed before files 11 and 12 change: X71 and
  X72 dev, X73 and X74 held out; a new kind, `loaded_table_final`, in each split.
- File 11's step 5 says a step is a CTE inside each final's query, never a block of its own;
  files 11 or 12 say a query and the Table it loads are read apart. Both files at most 8,000
  characters.
- At most two dev rounds, Haiku, arm C; then held-out once on the final files, Haiku and
  Sonnet, arm C, meeting ticket 18's thresholds on the whole split and on X73 and X74.
- `.venv/Scripts/python -m pytest`, the code review, the beginner reader and the drift review;
  CI passes; exported to main again.

## Answer
