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
| 2026-10-27 | 95fbcd5 | haiku | C | dev | 100 | 100 | 100 | 100 | 100 | 100 | 0 | 0 | 0 | 0 | 01:100 02:100 03:100 04:100 05:100 06:100 07:100 08:100 09:100 10:100 |
| 2026-10-27 | none | haiku | A0 | held_out | 0 | 100 | 100 | 0 | 0 | 0 | 90 | 0 | 0 | 1 | 01:0 02:0 03:0 04:0 05:0 06:0 07:0 08:0 09:0 10:0 |
| 2026-10-27 | none | haiku | A1 | held_out | 0 | 100 | 100 | 0 | 0 | 0 | 70 | 0 | 0 | 0 | 01:0 02:0 03:0 04:0 05:0 06:0 07:0 08:0 09:0 10:0 |
| 2026-10-27 | 95fbcd5 | haiku | C | held_out | 100 | 100 | 100 | 100 | 100 | 100 | 0 | 0 | 0 | 0 | 01:100 02:100 03:100 04:100 05:100 06:100 07:100 08:100 09:100 10:100 |
| 2026-10-27 | none | sonnet | A0 | held_out | 0 | 100 | 100 | 0 | 0 | 0 | 80 | 0 | 0 | 1 | 01:0 02:0 03:0 04:0 05:0 06:0 07:0 08:0 09:0 10:0 |
| 2026-10-27 | none | sonnet | A1 | held_out | 0 | 100 | 100 | 0 | 0 | 0 | 60 | 0 | 0 | 0 | 01:0 02:0 03:0 04:0 05:0 06:0 07:0 08:0 09:0 10:0 |
| 2026-10-27 | 95fbcd5 | sonnet | C | held_out | 90 | 100 | 100 | 100 | 100 | 100 | 0 | 1 | 0 | 0 | 01:100 02:100 03:100 04:100 05:100 06:100 07:100 08:100 09:0 10:100 |

## Routing (arm R), scored by hand

Each proxy read `copilot/00_start_here.txt` and named the one file it would load per task.

| date | files | model | split | routed as the task's objective | the others |
|---|---|---|---|---|---|
| 2026-10-27 | 95fbcd5 | haiku | held_out | 9 of 10 (90) | T03, "count ... and run it" (objective 01), to 03; T03 answered with 03 passes (`runs/2026-10-27-haiku-R-held_out/T03-with-03/`) |
| 2026-10-27 | 95fbcd5 | sonnet | held_out | 9 of 10 (90) | T03 to 03, as Haiku |

## Excel tasks, Copilot file 11 (`tools/excel_eval.py`)

One row per scored answers file. Arms: A0 the workbook alone; C file 11 with files 03, 04 and
05. "named" is the share of answers that name every refused piece, mark and thing left alone;
"code ok" the share whose Toolbox code parses and invents no name.

| date | files | model | arm | split | passed | found | parses | runs | correct | mapped | named | invented | code ok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-29 | none | haiku | A0 | dev | 0 | 100 | 100 | 90 | 75 | 0 | 70 | 5 | 0 |
| 2026-10-29 | 68effd5 | haiku | C | dev | 95 | 100 | 100 | 100 | 95 | 100 | 100 | 0 | 100 |
| 2026-10-29 | 44f6c5d | haiku | C | dev | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 0 | 100 |
| 2026-10-29 | none | haiku | A0 | held_out | 0 | 100 | 100 | 75 | 55 | 0 | 85 | 15 | 0 |
| 2026-10-29 | 44f6c5d | haiku | C | held_out | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 0 | 0 |
| 2026-10-29 | none | sonnet | A0 | held_out | 0 | 100 | 95 | 75 | 60 | 0 | 70 | 10 | 0 |
| 2026-10-29 | 44f6c5d | sonnet | C | held_out | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 0 | 100 |
| 2026-10-29 | a596632 | haiku | C | dev | 84 | 100 | 84 | 84 | 84 | 100 | 100 | 0 | 100 |
| 2026-10-29 | 67b7e92 | haiku | C | dev | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 0 | 0 |
| 2026-10-29 | 61c9ca2 | haiku | C | dev | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 0 | 100 |
| 2026-10-29 | none | haiku | A0 | held_out | 0 | 100 | 100 | 76 | 68 | 0 | 80 | 12 | 0 |
| 2026-10-29 | 61c9ca2 | haiku | C | held_out | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 0 | 100 |
| 2026-10-29 | none | sonnet | A0 | held_out | 0 | 100 | 100 | 84 | 64 | 0 | 84 | 20 | 0 |
| 2026-10-29 | 61c9ca2 | sonnet | C | held_out | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 0 | 100 |

From a596632 on (ticket 19), each split has 25 tasks, X41 to X50 added, and file 11 maps
HAVING, every JoinKind, UNION, MINIFS, the -IF forms and RANK. Dev rounds 1 and 2 are a596632
and 67b7e92, scored before X41's MINIFS gained a second condition (df822e4); 61c9ca2, after the
reviews' fixes, was checked on dev once, then scored on held-out.

| 2026-10-29 | 10de2a9 | haiku | C | dev | 94 | 100 | 97 | 97 | 97 | 100 | 100 | 3 | 51 |
| 2026-10-29 | fac0fd8 | haiku | C | dev | 97 | 100 | 100 | 100 | 100 | 100 | 100 | 3 | 0 |
| 2026-10-29 | none | haiku | A0 | held_out | 0 | 100 | 100 | 77 | 63 | 0 | 83 | 14 | 0 |
| 2026-10-29 | fac0fd8 | haiku | C | held_out | 94 | 100 | 97 | 97 | 94 | 100 | 100 | 0 | 97 |
| 2026-10-29 | none | sonnet | A0 | held_out | 0 | 100 | 100 | 83 | 60 | 0 | 91 | 9 | 0 |
| 2026-10-29 | fac0fd8 | sonnet | C | held_out | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 0 | 100 |

From 10de2a9 on (ticket 20), files 11 and 12 are loaded together, and each split has 35 tasks,
X51 to X70 added. Each run was answered in two halves of about 18 tasks, joined before scoring.
Dev rounds 1 and 2 are 10de2a9 and fac0fd8; held-out was scored once, on fac0fd8.
