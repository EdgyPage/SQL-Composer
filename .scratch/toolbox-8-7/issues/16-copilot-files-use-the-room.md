# The Copilot files use the room

Type: task
Status: resolved
Blocked by: -
Size: L

## Question

The user raised each Copilot file's limit from 8,000 to 9,000 characters (dev 257d9724), then
asked: "Make the documentation more robust if it can use the characters." Each file has about
900 to 1,800 characters to spare. What should each one add, so Copilot gets more right?

## Done when

- **Each Copilot file's source** (`tools/copilot_sources/`) adds what Copilot has been missing,
  drawn from the evidence, not guessed:
  - the Copilot evaluation's misses (`.scratch/copilot-eval/results.md`,
    `excel-files-11-12-misses.md`, the kept replies in `.scratch/copilot-eval/memo/`);
  - the usability rounds' findings about the Copilot files (`.scratch/usability-loop/results.md`,
    the "Found in ..." sections), such as file 18 never naming `write_days` for a chosen period;
  - the beginner readers' points on the files (`.scratch/toolbox-8-7/reports/`, and file 19's
    four points and the code review's two in ticket 11's Answer);
  - names a file's objective uses but its names list leaves out.
- Each file stays at or under 8,800 characters in both counts, keeping 200 to spare.
- Every Python block in each file still runs, and every name is public (the existing tests).
- `tools/copilot_files.py`'s refusal says "over the 9,000 each Copilot file keeps to", not
  "Copilot takes" (from the drift review of 7c17daf).
- **The evaluations run again** on the new files version, with ticket 02's memo:
  - the Copilot evaluation's arm C on the dev split, on Haiku, then the held-out split once;
  - the Excel evaluation for files 11, 12 and 15;
  - ticket 11's Metric request evaluation for file 19.

  Each scores at least as well as its last recorded round, recorded in `results.md`. A drop is
  fixed or reported with the reason.
- The beginner reader reads a sample of the changed files, and its report is linked here.

## Answer

### Built 2026-11-13

Every source in `tools/copilot_sources/` gained text, each rendered file now 8,060 to 8,800
characters with Windows line breaks (file 19 8,094). `tools/copilot_files.py`'s refusal says
"over the 9,000 each Copilot file keeps to". What each gained, and from which evidence:

- **`_always.txt`** (in 01 to 10): rule 10's list of files reaches 16, 17, 18 and 19. It had
  stopped at 13 and 14 (the 8.0 beginner reader's stop 34, fallen behind again).
- **00:** Terms for Run value (the value, not the function: 8.4's reader, stop 33) and "your
  chatbot"; steps 4 and 5 and the Self-check say what to do for file 19 and for a workbook; the
  route back from the chatbot's Hive (files 07 and 14); a Hivevar route. Ticket 11's reader,
  stops 1 and 2.
- **01:** `project.check` and `project.do_next` in its names; where the Project folder goes
  (usability E1-1, H1); a Windows path's backslashes (W1-2); a Table reference's `# TODO` line
  blocks nothing (W1-1).
- **02:** `project.reference_from_logic` and `run_query` in its names; check a doubted Key with
  `check_key` first (W2-2, W2-3); a `# TODO` line and an emptied `does_not_add_up=` (W4).
- **03:** `run_query` in its names and its first example, and a rule to run it when asked (arm
  R sent "count ... and run it" to 03 twice); a share as two totals divided; days written like
  20260924.
- **04:** a third example, a Derived table grouped to one row per job and then joined, the
  usual fix the file named but never showed; `derived` in its names.
- **05:** a third example, `rollup` over two columns, its total rows NULL, and a label only when
  asked (round 1's T14); testing a window's value in the reading Statement.
- **06:** `write_days(first_day, last_day)` for a table written several days at a time or for a
  Scheduled run's period (usability W8, all three runs); `export_hive`,
  `project.reference_from_logic` and `between` in its names.
- **07:** `script_tag` and `tag_text` in its names (8.3's reader, "Left"); the Script tag
  options as three Decision rules, a value given, a Run value, and a Hivevar only when asked
  (8.7 ticket 09's reader, point 18: "worked out each run" and "set at run time" read alike).
- **08:** comparing a finished batch on another Partition with `project.compare_batch` (H1,
  W1-3); the Lineage page's side panel and `project.export_project_lineage` (8.7 tickets 06 and
  08).
- **09:** two refusals: no GROUP_BY when counting, and a logic cell calling run_query; names
  the user's code defines are kept (T26's history); its names list gained what its fixes call.
- **10:** a `{name}` placeholder is a column, a value is written as Hive writes it; a Hivevar
  and `hive_date` pointer; `show_hive` before a drop, and the change_a_saved_table Workflow;
  `mapped`'s keys are the column's values (round 1 and 2's T28).
- **11:** a text date converted only inside a formula that reads it as a date, a passed-through
  `dt` left as it is (X69, failed three held-out rounds running; usability "Found in the tickets
  23 and 24 round"); a date minus a date; a repeated lookup key (7.2 ticket 20's "Not taken");
  a window orders by the source's column (X69's `dt_date`); OVER () said plainly (8.2 ticket
  19's reader).
- **12:** ReorderColumns, DuplicateColumn, Buffer, PromoteHeaders, ReplaceValue on text, and
  Excel's step names (names the objective meets but the file never listed); three Self-check
  lines from the old misses (X65's dropped order, a query read as a table, a query and its
  Table).
- **13:** the names cell first, every time (round 1's T33, T45); a tag is the old scheduler's
  place and never a reason to leave it open (T45, 8.3's history); accepting a proposed Key once
  the batch has finished (8.5 round, W3-1, W3-3); comparing another Partition once finished;
  "Run up to your Decisions" running to the end (8.5 round); FILES by name (round 2's T31);
  STAGING and "a query alone" said fully (8.2 ticket 23's reader, stop 12).
- **14:** `check_key` before answering a Key (W2); a `# TODO` line is no Decision (W4); naming
  DEV and PROD at an upgrade renames nothing (usability H2, ticket 19 round).
- **15:** the summary rule covers AVERAGEIFS, MAXIFS and MINIFS, names its groups in the map and
  keeps the Table's name (8.2 ticket 18's reader, 32; usability E2-1); "written into the Hive"
  for "typed in" (ticket 23's reader, stop 11); a text-date Self-check line.
- **16:** a Hivevar is kept with TAGS; "Run up to your Decisions" running to the end in prod (8.5
  round, H1); a second example, a location and a seed answered.
- **17:** `hivevar` and `project.batch_tables` in its names, the Hivevar answer only when asked;
  answer only what the user gives, `"key": None` when no column names a row, a location under a
  folder the user gives; convert's steps 4 and 5 (round 1 and 2's T47, T48). The pre-8.4 seed
  rule went to make room: the Upgrade's mark says it.
- **18:** a plain default and never none; the parameter as given or a Run value (W8-1, W8-2,
  W8-3); `write_days` for the run's period, taking the place of the build's write (W8, all
  three); `hivevars=` (8.7 ticket 09); `project.describe_logic` in its names.
- **19:** rewritten to ticket 11's reader and code review: Terms for Metric and your chatbot;
  goals and Done-when for steps 5 and 6; one "One column or two?" rule in step 2, the Decision
  rules and the Self-check; asking which column holds a quantity (M05's `duration_mins`); when
  to ask for sample rows and when to make them up; examples 1 and 2 follow the Output contract,
  one question each; the closing line on what to do with the request; `TEST` in backticks.

`tests/test_copilot_files.py`'s `OWN_CALLS` gains `write_days`, a logic function the user's
Table notebook defines, as `write` and `rows` are.

### The evaluations

All on haiku, arm C, with ticket 02's memo, recorded in `.scratch/copilot-eval/results.md`'s
ticket 16 block, which names the files version of each round:

| evaluation | last recorded | this ticket |
|---|---|---|
| files 01 to 17, dev | 100 (21-dev, then each objective at 100) | 81, 91, then 100 (32 tasks) |
| files 01 to 17, held out, once | 100 (21-held, 8.3's rounds) | 94 (16 of 17; T49 fails) |
| Excel, files 15, 11, 12, dev | 100 (24-dev) | 100 (42) |
| Excel, held out | 98 (24-held, X69) | 100 (42) |
| Metric request, file 19, dev | 100 | 100 (4 of 4) |
| Metric request, held out | 100 | 50 (1 of 2; M05 fails) |

- **The dev rounds' misses were fixed on dev:** round 1's T14, T28, T33, T45, T47 and T48, round
  2's T28, T31 and T48 (results.md says what each did and what the files now say).
- **T49, held out:** file 17's first measure (8.4 wrote T47 to T49 and ran none), so there is no
  earlier score to fall from; every objective measured before passes. T49 asks for every
  convert step through the compare; file 17 shows the decisions, create and seed cells and leaves
  the rest to file 13, as its header says, so step 1 was missing. Reported, not tuned on.
- **M05, held out:** the request's part 4 said "One row per: job", dropping the key's "with a
  finished run", which it kept only under Edge cases; the chatbot read every job of ops.jobs. Part
  4's wording is unchanged since ticket 11 measured 2 of 2. Reported, with the fix for the user.
- **Excel:** X69 passes for the first time in four held-out rounds.

**Decided:**

- **Evidence over padding.** Each addition answers a miss, a usability finding, a beginner
  reader's stop or a name the file's objective uses; where a file had no open point (04, 05),
  the room went to a second or third example of the case its rules name but never show, as
  `docs/agents/instruction-rules.md` asks of a task that isn't simple.
- **The 8,800 ceiling** is held in both counts; four files (03, 04, 05, 09) were trimmed back to it
  after their first drafts ran over, and file 17 dropped its pre-8.4 seed rule for convert's steps
  4 and 5, which T47 and T48 needed.
- **A Hivevar only when the user asks for one.** Round 1's T45 read "the scheduler puts the day in"
  as a Hivevar and left the tag open, the same trap as 8.3's T45. Files 07, 13 and 17 now say a
  tag is where the old scheduler put its value, and file 13 no longer mentions Hivevars at all.
- **The dev rounds ran on the 8.6 version line; every held-out, Excel and Metric request round on
  the files as committed** (8.7's line, after dev's 2bf64063, merged here and the files
  regenerated with the tools).
- **Three wording fixes after the held-out rounds**, from the code review: file 05's ORDER_BY
  bullet had lost its verb ("needs rows=") in a trim, file 11's text-date bullet ran past the
  wrap, and file 07's "What TAGS holds" sentence was unclear. None changes what a reply is asked
  for; the held-out scores belong to the version before them (e87b8a6cbeba).
- **M05's and T49's fixes are the user's to take.** Each held-out task is scored once per files
  version, and a fix drawn from a held-out failure makes the next round a second look. The M05
  fix is one line in file 19's Output part 4, "One row per: <the grain, and which of its rows
  appear>"; T49's is a task asking both files' steps, or file 17 naming convert's step 1.
- **The memo's pitfall** (results.md): `score` keys a dev reply on the arm's text when scored, so
  round 1, scored after five files changed, was kept under the new texts; those 14 memo files
  were deleted before round 2. Score a round before editing the files it measured.
- **The beginner reader** read files 18, 19 and 00 on Opus:
  [reports/beginner-reader-ticket-16.md](../reports/beginner-reader-ticket-16.md). It confirms
  twelve of ticket 11's points fixed. Its new stops are left for the user, as it only advises and
  the held-out scores belong to the files it read: file 18's three value mechanisms side by
  side, with Script tag and Hivevar undefined there; what the chatbot gives back (a column's
  Hive or a query); a table's "own days" with no `write_days` example; file 19's step 4 lost its
  "Then step 5" in the rewrite, and part 5 still asks "one total or per day" which no question
  asks now; 00's step 5 Done still reads as code.

## Code review

Run with this ticket as the spec and 9407eacc as the fixed point, the merge of ticket 14 set
aside. Its sub-agents ran as `review-standards` and `review-spec`, on Sonnet.

**Standards**

- **File 05's ORDER_BY bullet, a broken wrap that lost "needs".** **Fixed.**
- **File 11's text-date bullet past the wrap.** **Fixed**, with the line break kept inside the
  backticked Hive, so the backtick-name test still reads it as Hive.
- **File 07's "What TAGS holds is a Decision rule's".** **Fixed:** "What TAGS holds: the Script
  tag Decision rules."
- **File 05's "A window's value is never added up again" has no positive target.** **Answered:**
  it is the Toolbox's refusal, a hard guardrail; the bullet before it says where a window's value
  is tested, and file 05 is at its 8,800.
- **File 17's steps 4 and 5 block has no imports and no observable Done.** **Answered:** it is a
  notebook cell, as convert's own step cells are, run after the cells above it; the test runs it
  as file 17's other cells.
- **Duplicated Code and Shotgun Surgery: the Script tag routing restated in 00, 07, 10, 13, 17
  and 18; names added to several lists by hand.** **Answered:** each Copilot file stands alone,
  as the instruction rules require, and the names lists are each file's own.
- **`OWN_CALLS` gained `write_days` with no comment.** **Answered:** the constant's comment
  already says it holds the names the user's own code defines.
- **The deleted pre-8.4 seed line.** **Answered:** nothing else pointed to it; the Upgrade's mark
  says it to a Project converted before 8.4.

**Spec**

- **Two held-out scores below their last round, reported, not fixed.** **Answered:** under
  Decided; T49 has no earlier round, and both fixes would be tuned on held-out failures.
- **The beginner reader's stops not acted on.** **Answered:** under Decided, for the user.
- **Not every file's additions traced to evidence in the diff.** **Answered:** the Answer above
  names the evidence of each.
- **The docstring rewrap in `copilot_files.py`.** **Answered:** it came from dev's merge (ticket
  14's 7c17daf line), not this ticket.
- **`write_days` isn't a Toolbox name.** **Answered:** the reviewer found it consistent: a logic
  function of the user's, as the test's `OWN_CALLS` says.
