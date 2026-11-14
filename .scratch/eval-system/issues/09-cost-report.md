# The cost report

Type: task
Status: open
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
