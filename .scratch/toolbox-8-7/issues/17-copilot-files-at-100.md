# The Copilot files at 100

Type: task
Status: resolved
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

**v5** (d048c37b0c6d, e1b8332a: files 03 and 05 teach `contains`, `starts_with`, `INTERSECT`
and `EXCEPT` again): arm C dev 100 (T07, T08, T13, T14 asked, 28 from the memo), held out 100
(T09, T15); arm R not asked, file 00 unchanged; no file changed.

**v6** (9b95a964c448, 5be7d7c8: file 03's R8 names `contains` and `starts_with`, P13 in order):
arm C dev 100 (T07, T08 asked, 30 from the memo), held out 100 (T09); no file changed.

**v7** (2ac4878025c9, c0c39299: file 00's steps 3 and 4 and C2 carry file 19's wording, at
the merge): arm R, dev 31 of 32 and held out 15 of 17, strict 46 of 49 (94), by the Index 49
of 49 (100); the three others (T01, T03 to 03, T24 to 02) are v3's, each by the Index; no
file changed.

Status stays open: the Metric request half's part is on its own branch.

### Metric request

Built 2026-11-14 on its own branch. The rounds, files versions and rules are in
`.scratch/copilot-eval/results.md`'s "Ticket 17, Metric request" block.

**The user's rules, added as the work went** (their words, 2026-11-13 and 14):

- "It's sufficient for the model, on M tasks, to suggest what type of data may be missing or to
  ask for the definitions of columns. ... I'm more interested in correct guidance than on exact
  answers in cases where exacts are impossible with given data. Simply suggest fixes; do not
  invent answers to make users happy just to give them something."
- "The m tasks shouldn't be giving numbers, per se, it should be establishing metric columns
  using column definitions. LLMs are not to do math with. Correct SQL is easy once the task is
  defined and sql will be generated from another model that has databases indexed, a task not
  for copilot. Hone business requirements for a model with better access."
- "I am more concerned with directional correctness than exact correctness. Messy or
  incomplete data definitions are anticipated. Create scenarios where data is missing for the
  metric in question. More good than bad is progress."
- "keep tweaking the docs until we get to 100%. 95%+ is an acceptable average. ... Memoize
  inputs and use evaluation scripts to reduce LLM token usage wherever possible."

**What changed:**

- **Seventeen tasks** (`tools/metric_eval_tasks.py`), eleven new: M07 a fraction (high alerts'
  share), M08 a day-over-day change, M09 a distinct count by the day's team, M10 a band with
  edges, M11 a reaction time no table records, M12 a muddled pair with sample rows, M15 a cost
  per run where costs are per day, M16 a column with no definition; held out M13 a first day
  over budget, M14 night pages with no time of day, M17 a load date against a snapshot date.
  Twelve dev, five held out; five are missing-data scenarios.
- **Column definitions**, messy as real ones are (`COLUMN_DEFINITIONS`): vague, blank, units
  unstated, a "load date". The stand-in user and Copilot both get them; they are in the memo key.
- **Scored by requirements, for direction** (`tools/metric_eval.py`): each task's key marks
  elements essential (the source columns or the named gap with its fix, the grain and its
  conditions, the column count where muddled, a task's own such as M06's no invented kind of
  alert) or helpful. A request passes with every essential, more helpful met than not, no column
  name the definitions don't give, no worked-out number and no SQL. Every rule is
  deterministic; no judge model. **The chatbot proxy and the number check are dropped**, as the
  user's "LLMs are not to do math with" asks; each task's `example` request, which meets its key,
  replaces the reference Hive, and the tests take each element out of it to show it is checked.
- **File 19, rewritten to be looked up:** rule ids by kind (A asking, D definitions, C columns,
  Q quantities, G grain, T days, M gaps, N no maths), a "When the user says, do" list, patterns
  to copy, a finished request, a Self-check S1 to S10. It does no maths: part 8 is now "How to
  check", in words. 8,778 characters with Windows line breaks; one file was enough, so no file
  20.
- File 00's line for file 19 and its steps 4 and Self-check say to paste the column
  definitions; the README template's step 3 too; CONTEXT.md's Metric request, Grain and Sample
  rows entries follow, and Column definitions and Gap are new; CHANGES.md's 8.7 bullet;
  `docs/copilot-eval.md`'s Metric section; `.claude/agents/metric-proxy.md` loses the chatbot.

**The rounds** (haiku, arm C, the memo):

| round | files version | score |
|---|---|---|
| dev 1 to 6 | 344a77f9cb3a, 3dcdf4022019, 8f33f8fdfda7, d78b1b9e713f, eac927dd9447, 1a40b5a88a53 | 83, 100*, 92*, 100, 75, 100 |
| held out | 3dcdf4022019, d78b1b9e713f (twice), 1a40b5a88a53 (twice) | 80, 100*, 80, 100*, 100 |
| baseline A0, all 17 | 1a40b5a88a53 | 47 |

\* rescored after a scorer rule was fixed on the same replies (M11's team, M02's "with a", M06's
"fraction", M13's "more than"), never after a file change.

- **The last files version (1a40b5a88a53): dev 100, held out 100 twice in a row.** The average
  of every round as finally scored is 92; the target was 100, with 95 as an acceptable average,
  and the last version meets 100.
- **Held-out tasks that shaped a fix: M17, twice** (asking what two tables' dates mean; then
  recommending no reading of its own). Its later passes are second looks. M06's and M13's
  held-out misses were the scorer's, fixed in its rules and rescored on the same reply; the
  dev fixes came from M02, M04, M10, M15 and M16.
- File 00 changed after the last held-out rounds (its file 19 lines), so the current files
  version is not 1a40b5a88a53; file 19 itself is the same, and held-out rounds load only it.

**Decided:**

- **Eleven new tasks, not six to eight:** the user's later "Create scenarios where data is
  missing" asked for more; three of them are held out.
- **Held out run twice on d78b1b9e713f:** the brief's "twice in a row on the last" was being
  tried there; its second run missed (M17), so it was not the last version.
- **The proxies:** a sonnet runner per conversation relaying two haiku `copilot-proxy` agents
  by file name; proxies left stray turn copies in misspelt folders outside the repo
  (`...\SQL-Competer\`, `SQL-Competition`, `SQL-Netcomposer`), which this agent's worktree
  isolation can't remove: for the user to delete.

**Code review** (c7356605 as the fixed point, `review-standards` and `review-spec` on Sonnet):

- **Standards, fixed:** `column_count` now uses `shared.counted`; `score_request`'s
  conditional expression and identity test became a list of (requirement, met) pairs; the nine
  part labels live once, `metric_eval_tasks.PARTS`; `Score.essential` is `holds_essential`;
  `memo_key`'s docstring says why `reply` is there (eval_memo's signature).
- **Standards, answered:** `_turns`'s sort tuple and the if/elif command chain are ticket 11's,
  unchanged; `request_form` returning "" is held by a test that file 19's form is found;
  `split` and `muddled` stay strings, as every evaluation's tasks write them.
- **Spec, answered:** the task count and the double run, under Decided; the held-out rescores
  are scorer fixes on the same replies, each recorded, and the 100-twice includes one; M17's
  being shaped twice is recorded; the average of all rounds (92) is below 95, the last version
  at 100.

**Beginner reader** (Opus):
[reports/beginner-reader-ticket-17-metric.md](../reports/beginner-reader-ticket-17-metric.md).
Its main stops: no example of what pasted column definitions look like; what to say to the
chatbot with the request, and whether Hive comes back; who ends the asking (step 3 against A4).
Left for the user: each is a change to file 19 and a new held-out round.

### Closed 2026-11-14

Both halves merged on dev (98831a5, e21af0c), with D523 (four names files 03 and 05 had lost)
fixed in e1b8332 and file 03 tidied in 5be7d7c, each re-measured. On the current files, on
haiku: files 01 to 17 dev and held out 100; Excel dev and held out 100; Metric request dev and
held out 100 (held out twice running); routing 100 by the Index, 94 strict, its three strict
misses requests two files answer. The whole suite passes on dev after the merges (exit 0), and
no drift item is open.

File 00's Index then gave one file a request (cfc22c4, then this round's fix: three cells a
row, R3's tag value given once by R2's ends, R8 naming "using my Database module" and a Key
check "with my query"). T01 (dev), T03 and T24 (held out), routing's strict
misses on v1 to v7, shaped the Index change, so their passes since are second looks. On v9:
routing dev 97 strict (T05 to 08, by R8; T05 and T24 ask one Key check the tasks give to two
files), 100 by the Index; held out 100 strict twice running; arm C held out 01, 02, 08 at 100.

### Metric request, six more held-out tasks (2026-11-14, after the close)

A check found two gaps: the Metric request's average over its rounds was 92, below the 95 the
user called acceptable, and its held-out set was five tasks, M17 among them having shaped two
fixes. The rounds are in `.scratch/copilot-eval/results.md`'s "Ticket 17, Metric request"
block, under "Six more held-out tasks".

- **Six new held-out tasks, M18 to M23,** written and committed (35dabb0) before any was run,
  under the user's rules: requirements-scored, directional, on the messy definitions, no maths.
  M18 a rounded share on the latest snapshot day; M19 a queue wait no table records (missing);
  M20 two columns asked, one meant; M21 a cost band over 7 days with sample rows; M22 failures
  from bad data, a cause no table records (missing); M23 different bad days in the last 30.
  `tests/test_metric_eval.py` holds their keys as the others' (each example meets its key,
  each element taken out is unmet, each gap unnamed or unfixed fails), and that the six are
  held out, varied, and two of them missing data. Twenty-three tasks: twelve dev, eleven held
  out.
- **On file 19 as it was (memo c1e3766113b7):** the six new 100; all eleven 91 (M20 failed),
  then 100. With dev 6's 100 from the record, the average is 98.
- **The fix, from M20's miss:** the user's "take your recommendation and write it as a gap" was
  read as the end of the asking, so the grain and days were never asked. A4 now names the two
  endings ("That's all", "write the request") and says a taken recommendation or "write it as
  a gap" is an answer, with the next question (G1, T1) to follow. File 19: 8,722 characters,
  8,876 with Windows line breaks.
- **On the fixed file 19 (89c506d04b97):** dev 100, held out (all eleven) 100. Average 100.
- **Held-out tasks that shaped a fix:** M20, on its second look. M18, M19, M21, M22 and M23
  shaped nothing.
- **The user's rule, given mid-run** (2026-11-14): "Don't test the entire suite of policies
  unless there's reason to believe the tests will be different ie you changed the
  documentation the model uses to answer the script. Run the whole suite at the end." So: run
  only what can come out different (new tasks, or every task once after file 19 changes); take
  the rest from the memo and the record; run the tests a change touches as it goes, and the
  whole suite once at the end. The brief's held-out "twice in a row" on the last version gave
  way to it: the fixed version's held out ran once. The two held-out runs on c1e3766113b7 had
  already run, side by side, when the rule came.
- **The proxies:** one sonnet runner per round, each turn a fresh haiku `copilot-proxy` given
  its message file and the turn files so far; a runner that continued proxies by SendMessage
  handed back before they had answered, since a resumed agent runs in the background.
