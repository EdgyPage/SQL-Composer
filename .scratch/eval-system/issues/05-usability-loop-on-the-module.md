# The usability loop on the module

Type: task
Status: open
Blocked by: 01, 02
Size: M

## Question

The usability loop keeps its own memo and its runs in git (Q2, Q4, Q9).

## Done when

- `usability_loop.py` keys each scenario's memo through `eval_runs` (its inputs as today), writes
  runs, transcripts and results under `.eval-local/`, and records each phase agent's and routed
  question's usage in the ledger.
- `prepare` prints the one-line prompt to spawn each phase's agent; routing a question prints the
  proxy to spawn, as ticket 03's batches do.
- `docs/usability-loop.md` says how in numbered steps.
