# Copilot evaluation results

One row per scored answers file (`tools/copilot_eval.py score ... --record`). Rates are percent
of the run's answers; needless, star and unrun are counts: opt-outs or Unchecked pieces no
reference needed, star imports, and answers that don't run what the request asked to run.
Arms: A0 the request alone; A1 the README's opening, cut to 8,000 characters; C the task's
Copilot file; R routing by `copilot/00_start_here.txt`. Runs keep their message and answers in
`runs/`.

| date | files | model | arm | split | passed | found | parses | builds | runs | correct | invented | needless | star | unrun | per objective |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-27 | none | haiku | A0 | dev | 20 | 100 | 100 | 30 | 30 | 25 | 60 | 0 | 0 | 1 | 01:50 02:50 03:0 04:50 05:0 06:0 07:0 08:0 09:50 10:0 |
| 2026-10-27 | none | haiku | A1 | dev | 30 | 100 | 100 | 50 | 50 | 35 | 20 | 0 | 0 | 1 | 01:50 02:50 03:50 04:50 05:0 06:0 07:0 08:0 09:100 10:0 |
| 2026-10-27 | 353cbeeb | haiku | C | dev | 100 | 100 | 100 | 100 | 100 | 100 | 0 | 0 | 0 | 0 | 01:100 02:100 03:100 04:100 05:100 06:100 07:100 08:100 09:100 10:100 |
