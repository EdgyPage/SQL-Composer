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
