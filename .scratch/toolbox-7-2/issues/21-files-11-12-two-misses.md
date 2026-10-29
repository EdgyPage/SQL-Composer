# Files 11 and 12: the two held-out misses fixed, and held-out scored again

Type: task
Status: resolved
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

Built 2026-10-29. Tasks X71 to X74 (02f8d5e) before any file change; then step 5 and the
loaded Table rule (aa75911), file 11's step 2 made to agree with it (6fc91ff, from the drift
review), and the reviews' wording with UPPER, LOWER and TRIM put back (f80b90b).

| run | files | passed |
|---|---|---|
| dev round 1, Haiku C | aa75911 | 97: X54, a Table from another workbook in the batch |
| dev round 2, Haiku C | 6fc91ff | 100 |
| held-out, Haiku / Sonnet C | 6fc91ff | 97 (X73) / 100 |
| dev check, Haiku C | f80b90b | 97: X54 again |
| held-out, Haiku / Sonnet C | f80b90b | 92 (X61, X70, X73) / 100 |

**Cause 1, a step written as a block of its own, is fixed:** X69 and the new X72 and X74 pass
in every run since.

**Cause 2 is not, for Haiku.** X73, new and unseen, failed on 6fc91ff, and X70 and X73 on
f80b90b, the same way each time: a query and the Table it loads share a name, another query
reads the query, and Haiku takes the Table for the step, dropping the final and its formula
columns. Sonnet gets it right in every run. X61 on f80b90b named Tables of another workbook in
the batch, as X54 does on dev.

Haiku's held-out score across the three file versions is 94, 97 and 92: within a task or two of
95% either way. f80b90b's 92% misses the threshold; 6fc91ff's 97% met it, but f80b90b, with
UPPER, LOWER and TRIM back, is the version to ship. Tuning has used every round the rules give.

**Reviews:** standards (sonnet) none; spec (sonnet): UPPER, LOWER and TRIM had been cut, put
back in f80b90b; beginner reader (opus): step 2's and step 7's wording, taken in f80b90b, and
that no worked example shows a query and its loaded Table read apart, which file 11 has no room
for. Drift: 02f8d5e, aa75911, 6fc91ff, f80b90b clean.

**Left:** the user's call: ship f80b90b as it is, or give file 12 a worked example of a query
and the Table it loads, with new held-out tasks for it.
