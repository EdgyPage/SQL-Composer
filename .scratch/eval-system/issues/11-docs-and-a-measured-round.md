# The docs and a first measured round

Type: task
Status: open
Blocked by: 09, 10
Size: S

## Question

The instructions are what travels between machines (Q9): can a fresh agent run a round from
them alone, and what does a round cost now?

## Done when

- `docs/copilot-eval.md` and `docs/usability-loop.md` are numbered steps a fresh agent follows
  with no other context; CLAUDE.md points at them and at `.eval-local/`.
- One small round per pipeline runs on the new system (only what the memo says changed, by the
  user's rule), recorded in the ledger.
- The report shows each pipeline's cost per round beside 8.7's known figures (about 580k to 720k
  tokens per ticket's orchestration), and the ticket's Answer gives the difference.
