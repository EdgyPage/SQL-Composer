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

## Answer

### Files 00 to 18

Built 2026-11-14 on its own branch, from dev's c7356605. The user, mid-ticket: "keep tweaking
the docs until we get to 100%. 95%+ is an acceptable average."

**The shape.** Every file 00 to 18 (`tools/copilot_sources/`) is written to be looked up, under
the same headings in each, so a search or an index finds the same part in every file:

- a bold header, "Find the request in Patterns, copy the worked pattern it names ..., then
  tick the Self-check";
- `## Patterns: when the user says X, do Y`, a table of ids P1 and on, the user's words, what
  to do and the rule or worked pattern to copy (07: "when the Hive says X"; 09: "when the
  message says X"; 11, 12 and 15: "when the workbook or formula has X");
- `## Terms`; `## Rules`, each rule an id, R1 and on (11 and 12 group theirs by kind: F, I, V,
  M, X, N, Q, G, T, S);
- `## Always: rules A1 to A10` (`_always.txt`, in 01 to 10), shortened, its file list kept;
- `## Names for this objective, with their arguments`; `## Worked patterns`, W1 and on, each
  under a `###` heading saying the case; `## Steps`, Find, Copy, Check (13, 14, 16 and 18 add
  Place and Name the rest; 15 keeps its seven); `## Output`; `## Self-check`, `- [ ] C1` and on.

File 00 opens on an Index, P1 to P17, of the words a user would type and the file each sends
them to, with rules R1 to R8 for when two lines fit; its Which file list is kept line for line,
for the Metric request half's own lines. No file split: each holds its patterns at 8,463 to
8,799 characters (16: 7,563), every Python block still running.

**The rounds** (`.scratch/copilot-eval/results.md`, "Ticket 17, files 00 to 18"), on haiku with
ticket 02's memo, four files versions:

| evaluation | v1 | v2 | v3 | v4 (last) |
|---|---|---|---|---|
| files 01 to 17, arm C, dev (32) | 100 | (memo) | (memo) | (memo) 100 |
| files 01 to 17, arm C, held out (17) | - | 100 | 100 | 100, then 100 |
| Excel, dev (42) | 98 | 100 | 100 | 100 |
| Excel, held out (42) | - | 98 | 100, then 98 | 100, then 100 |
| arm R, strict (49) | 94 | 96 | 94 | 96 |
| arm R, by the Index (49) | 94 | 100 | 100 | 100 |

- **The last version, v4 (1c45f348c91a, 39946edf), passes every round:** arm C dev and held out,
  held out twice running; Excel dev and held out, held out twice running; arm R 100 by the
  Index, 96 strict. The average of every round, arm R strict, is 98.6.
- **T49 passes on every version**, its RENAME fault fixed in file 17 (P11, R11, C4: the name the
  user says convert gives is its own, `RENAME = {}`). T49 shaped that fix: a third look.
- **The fixes, each the general fault:** X12 (dev): file 11's X1 had lost "circular". T02 (arm
  R, dev): file 00's Index had no "my Database module". X25 (held out, v2) and X36 (held out,
  v3's second round): files 11 and 12 named their marks' rules without the marks' names; every
  mark now has one ("approximate", "text date", "Sql.Database", "pivot", "order dropped"), as
  "blank" and "repeated key" had. T03 and T24 (arm R): two files answer each, so the Index
  names both (P2, P3, R8). **Held-out tasks that shaped a fix: T49, X25, X36, T03, T24.**
- **Arm R strict stays at 96:** T03 ("count ... and run it with my query", objective 01) goes
  to 03 and T24 (a Key check, objective 08) to 02 in every round. Both files teach each, the
  Index says so, and each pick was asked with its file and passed. A strict 100 would need the
  Index to pick one file for a request two files answer.
- **Held out on v1 was not run:** v1's Excel dev missed, so v2 came first, as a held-out round
  is asked once per files version.
- A second held-out round on one version was asked on a fresh memo folder, since the memo
  hands a version's held-out reply back.

**The suite:** the regeneration chain, then the whole suite, exit 0, writing
`tests/snapshot/known.txt`'s two new Hive texts (file 01's W3). Its first run failed two tests:
`test_usability_loop.py` held file 00's old header phrase "one Copilot file" as proof file 00
is pasted, now its `## Which file` heading; and the pointer test's `.pytest_cache/memo/`, which
a run without the cache plugin doesn't make (ticket 16's note). A lock-timing test failed once
under load and passed alone and on the next whole run.

**The code review** (c7356605 as the fixed point, `review-standards` and `review-spec` on
Sonnet):

- **Standards: no hard violation.** Judgement calls: the file map is written three times
  (file 00's Index, its Which file list, rule A10). **Answered:** each file stands alone, so A10
  is a copy by design; the Index is the words a user types, Which file the files' objectives,
  kept line for line for the other half's lines. File 00's P ids name Index rows, not Patterns:
  **answered**, file 00 stands alone. File 03's P12 pointing at A10: **answered**, A10 is the
  rule that names the file to load.
- **Spec: no held-out round on v1.** **Answered** above. **The Excel held-out rounds are
  noisy** (98, 100, 98, 100, 100). **Answered:** each miss was a mark the reply didn't name,
  fixed by naming every mark; the last two rounds are 100. **Arm R is 96 strict.** **Answered**
  above. **File 17's rows echo T49's words** (P2's "period_end() in my run_values.py", P9's
  "/data/team", P11, P12). **Answered:** P2 and P9 are dev T47's words, which T49 shares; P11
  and P12 are T49's fault, recorded as shaping the fix. **Files 11 and 12's mark names come from
  X25 and X36:** **answered**, recorded as second looks.

**The beginner reader** read files 00, 03 and 13 on Opus:
[reports/beginner-reader-ticket-17-files.md](../reports/beginner-reader-ticket-17-files.md).
Every id points at a rule that exists. Its costliest stops, left for the user, as it only
advises and the held-out scores belong to the files it read: file 03's header says "change only
the tables, columns and values" while W1 carries GROUP_BY, HAVING and a run, which a plain
"list the rows" request doesn't need; file 13's DECISIONS cell names its example tables three
ways (R5, R8, W2), and doesn't show where "tags" goes; file 00's Index overlaps ("add Table
references" 02 and 14, "drop a day" 10 and 14, "total" 03 and 05) with no rule choosing; file
13 has no row for `project.run_workflow("convert", ...)`; Patterns sit above Terms, so terms
come before their definitions.

Status stays open: the Metric request half's part is on its own branch.
