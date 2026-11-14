# The docs and a first measured round

Type: task
Status: resolved
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

## Answer

Run 2026-11-14, by the session alone, following the docs' numbered steps: no orchestrating
worker, each proxy spawned from the line its batch printed.

**The docs.** Tickets 03 to 05 and 09 made `docs/copilot-eval.md` and `docs/usability-loop.md`
numbered steps (plan, batch or prepare, spawn, collect, score, record, report). CLAUDE.md now
points at both for a round, and at `.eval-local/` for every record; its line that the old
pipelines still write under `.scratch/` is gone.

**What the plans asked**, by the user's rule (only what changed):

| Pipeline | Asked | Why | Tokens | Result |
|---|---|---|---|---|
| Copilot C, dev and held-out | 0 of 49 | every key unchanged | 0 | 100% |
| Copilot R (routing), dev | 32 | never kept: R was scored by hand before ticket 03 | 77,146 (4 haiku proxies) | strict 100%, Index 100% |
| Excel C, dev | 0 of 42 | unchanged | 0 | 100% |
| Metric request C, dev | 0 of 12 | unchanged | 0 | 100% |
| Usability, W5 run 1 | 1 of 49 runs planned | the Toolbox and Copilot files changed since 8.6's runs | 101,908 (one phase agent) | pass, 0 questions |

The held-out tasks first planned as changed: their kept replies were keyed with the Copilot
files' version, which keys made now leave out. Their loaded-text hashes were exact, so the 247
kept replies were re-keyed without it (the carry-over ticket 01 planned), and the plan then took
all 17 from the memo.

**The difference.** All five rounds together cost 179,054 tokens, against 580,000 to 720,000 for
one ticket's evaluation orchestrated by an Opus worker in 8.7: 3.2 to 4 times less for all
pipelines at once, and 7.5 to 9.3 times less comparing the routing round alone. The saving is
the memo, which asked nothing of the 103 unchanged tasks, and no orchestrator, whose own reading
was most of 8.7's figure. A Metric request conversation alone costs 4.2 times less on one agent
per role (ticket 04: 44,636 against 188,596 tokens). The report, `.eval-local/report.html`,
shows each round beside the baseline in `.eval-local/baseline.json`.

**Left.**
- The usability loop's other 48 planned runs are not run: this ticket asks for one small round
  per pipeline. They are the next usability round's, when the user asks for one.
- The `zero-context-user` and `metric-proxy` agent types were not registered in this session
  (Claude Code reads agent files at a session's start). W5's phase agent was a general-purpose
  haiku agent given the role's text and the same tool limits; a fresh session spawns the real
  type.
- In the ledger, the maintainer agents' drift reviews are the largest cost so far, 9 runs and
  701k tokens, which opened 2 items. The build agents of tickets 01 to 10 (about 2.0M tokens,
  kept beside the ledger, since the ledger takes no build rows) were larger still. What to change
  is the user's decision (ticket 08: the data decides later).
