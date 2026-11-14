# The cost report

Type: task
Status: resolved
Blocked by: 03, 04, 05, 06, 07, 08
Size: M

## Question

The user: "html exports make sense to me to analyze eventful commits and version changes."
(Q3, Q14.)

## Done when

- `tools/eval_report.py` writes `.eval-local/report.html` from the ledger and the attribution
  records, built with `sqlglot_composer/html_page.py`, offline:
  - tokens per round, pipeline, model, Toolbox version and commit;
  - eventful commits marked: a version raise, a Copilot file change, a ticket's merge;
  - pass rates beside cost;
  - the doc ids failing replies cite most, per file, from ticket 06;
  - the maintainer agents' share of all tokens, from ticket 08.
- A test builds it from a small ledger fixture.

## Answer

Built 2026-11-14: `tools/eval_report.py`, tests in `tests/test_eval_report.py`, a `report` step
in `docs/copilot-eval.md` (7) and `docs/usability-loop.md` (12).

    .venv/Scripts/python tools/eval_report.py [--local DIR] [--commits FILE] [--baseline FILE]

It writes `.eval-local/report.html` with the page module: cost per round, pipeline, model,
version and commit (with totals by pipeline, model and version); eventful commits with the
tokens recorded on each; pass rate, `OVER CAP` count and tokens a pass per round; the ids
failing replies cite, per file (ticket 06's `attribute`); the maintainer agents' share
(ticket 08); and a Baseline section.

**Decided:**

- No subprocess, so git's facts are a file, `.eval-local/commits.txt`, made with one command the
  docs give: `git log --format="commit %h %cs %s" --name-only -n 600 > .eval-local/commits.txt`.
  A commit touching `version.txt` is a version raise, its version the first number of its
  subject; a row's version is the latest raise at or before its commit; `copilot/` or
  `tools/copilot_sources/` is a Copilot file change; a merge subject ending `(<map> ticket NN)`
  is a ticket merge. No file: the page builds with no versions or marks. No `ALLOWED` or
  `AUDITED` entry was needed.
- Baseline figures are `.eval-local/baseline.json`, a list of `{label, low, high}`; ticket 11
  fills it and adds the comparison.
- Pass counts come from ledger results starting `pass` or `fail`, else from the kept sources
  rows (the usability loop's results are `done`/`stuck`). `OVER CAP` is counted where the
  session keeps it in the ledger result.

## Code review

Run with this ticket as spec, fixed point 1ea285ef (review-standards and review-spec, sonnet).

- Fixed: a commit touching `version.txt` whose subject names no version is not a raise (it gave
  "?"); `events_of` was reached through a needless lookup.
- Answered: `git log --name-only` lists no files for a merge, so a raise or Copilot change
  arriving only through a merge is unseen; the commits are linear on dev, which is where the
  ledger's commits are. Commits older than `-n 600` show version "-". The `numeric` column
  sets, the extra Tokens-a-pass and Result columns, and the two doc steps are kept.
- Left, as judgement calls: renaming `one`, `count`, `note`, `section`; small repeated
  recomputation; a plain loop in `grouped`; `read_commits` builds parallel lists; the doc steps
  carry the command inline.
