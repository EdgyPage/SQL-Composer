# Scoring Copilot on the Copilot files

The Copilot files (`copilot/`) should make Microsoft Copilot write Toolbox code that works. This
measures it against the same tasks and scorer, whether a proxy model answers in a Claude
session (a round by script, below) or you ask Copilot's web chat by hand. Tasks:
`tools/copilot_eval_tasks.py`, scorer: `tools/copilot_eval.py`; the Excel tasks and scorer
are `tools/excel_eval_tasks.py` and `tools/excel_eval.py`. Everything reaches only this
computer.

Run every Python command with `.venv/Scripts/python` from the repo's top folder. Nothing a
round writes is tracked: runs, the memo, the ledger and `results.md` are all under
`.eval-local/`, which git ignores, so never copy one into a tracked file. Of a Copilot
round, `.eval-local/copilot/runs/<round>/` holds a folder per proxy (its `message.md` and
`answers.md`) and the round's merged `answers.md`; of an Excel round,
`.eval-local/excel/runs/<round>/`. Both tools add a row per scored round to
`.eval-local/copilot/results.md`.

## A round by script: the steps

A round has no orchestrating agent: a script plans it, writes each proxy's message, collects
the replies, scores them and keeps them, and you spawn only the proxies, each with the one line
the script printed. Follow these in order. `<round>` is a new name you choose, such as
`2026-11-15-c03`; a name used before is refused.

1. **Plan.** Choose the arm and the tasks, and run:

       .venv/Scripts/python tools/copilot_eval.py plan C --split dev --objective 03 --model haiku

   The arm is `C` (the task's objective file), `R` (routing: which file to load from file 00),
   `A0` (nothing) or `A1` (the README's opening); `--split` is `dev`, `held_out` or `all`, and
   `--objective` is one of the files' numbers. The plan says of each task `ask:` and why (no
   reply kept, its text changed, the text it loads changed, or `--fresh`), or `from the
   memo`; how many proxies to spawn; and the round's estimated tokens from past ledger
   rows. `--fresh` asks every dev task again, kept or not; a held-out task is asked once per
   version of the text it loads, so `--fresh` leaves it. If the plan is over its budget,
   `--over-budget` runs it anyway. Excel: `.venv/Scripts/python tools/excel_eval.py plan C
   --split dev --tasks X01,X02,X03,X04,X05 --model haiku`.
2. **Batch.** The same command, every flag the plan had (`--fresh` too), with `batch` and
   `--round <round>`:

       .venv/Scripts/python tools/copilot_eval.py batch C --split dev --objective 03 --model haiku --round <round>

   It writes each proxy's message file and prints one line per proxy:
   `<agent type> | <model> | <prompt>`. If it prints `Nothing to ask`, skip to step 4.
3. **Spawn.** For each line, spawn one agent of that type on that model, with that prompt
   exactly and nothing else, all in one message so they run together. The proxy reads its message
   file and writes its answers file, and has no other tool. Note each one's tokens and seconds,
   which Claude Code reports when it finishes, and name each by its folder under the round's
   (the prompt names it: `c03`, `r-1`).
4. **Collect.**

       .venv/Scripts/python tools/copilot_eval.py collect <round>

   It merges the proxies' answers files into the round's `answers.md`, and says which proxy
   wrote none and which tasks have no reply. Spawn that proxy again if one failed, or go on:
   a task with no reply is scored from the memo where one is kept, and reported where not.
5. **Score.**

       .venv/Scripts/python tools/copilot_eval.py score <round>

   It scores each reply, and for each task of the round the proxies didn't answer, the
   reply the memo keeps for it now; keeps every reply with its score line in the memo; prints
   the report and how many replies came from the memo; and adds a row to
   `.eval-local/copilot/results.md`. Score a round before editing the files it measures: a dev
   reply is kept under the text it was scored on.
6. **Record.** For each proxy, with the tokens and seconds it reported:

       .venv/Scripts/python tools/eval_runs.py record --pipeline copilot --role proxy --round <round> --task <folder> --arm C --model haiku --tokens <tokens> --seconds <seconds> --result "<passed of asked, such as 3 of 3 pass>" --commit <git rev-parse --short HEAD>

   `<folder>` is the proxy's folder, as step 3 named it (`c03`, `r-1`). Use `--pipeline
   excel` for an Excel round. `.venv/Scripts/python tools/eval_runs.py ledger`
   prints the ledger, whose rows are the next round's estimates.
7. **Report.** First write the commits file, which gives the report each commit's version and
   events (without it the page builds with neither):

       git log --format="commit %h %cs %s" --name-only -n 600 > .eval-local/commits.txt

   Then `.venv/Scripts/python tools/eval_report.py` writes `.eval-local/report.html`: cost,
   pass rate, eventful commits and the doc ids failing replies cite, from the ledger and the
   pass count each `score` keeps in `.eval-local/rounds.csv` (every reply, the memo's too, so a
   round the memo answered whole shows at no cost).

Arm R scores routing and nothing else: each proxy replies with a file name per task, and `score`
gives, per task and in total, two rates, both with no model. **Strict**: the reply names one
file, and it is the task's objective's file, as the rules the proxy was asked under say. **By
the Index**: the first file it names is one file 00's Index loads for that objective, read
from the Index as it is now, so an edit to the Index changes the score. A reply naming file 00,
a file that doesn't exist, or none, fails both. Its results row is `| date | files | model | R |
split | replies | strict | index | from the memo |`.

## The memo: ask only what changed

Every reply is kept with its score in `.eval-local/memo/`, one plain file per key, so a round
asks a model only the tasks whose text changed. A reply's key is:

- the task's id and text, the prompt it is asked;
- the arm;
- the model, `copilot-web` for Copilot's web chat;
- the hash of exactly the text the task loads before the prompt: nothing in A0, the README's
  opening in A1, the task's objective file in C, file 00 and the file the reply names in R, and
  files 15, 11 and 12 for an Excel task in C.

Dev and held-out tasks are kept alike. A held-out task is asked once per version of the text
it loads (an edit to another file leaves it), and `--fresh` doesn't ask it again. Each memo file
holds its key, the date it was asked, its score line, then the reply as it came.

## Sources: which rule a failing reply followed

A proxy ends each answer with a `Used: ` line naming the patterns, rules and worked patterns it
followed (`Used: P3, R7, W1`, each with its file's number, `11:F4`, where the message holds
several files), and Copilot in a Metric request conversation does the same at the end of each
of its turns. An id is one a file defines: a Patterns row, a bullet such as `- **R7**` or `- A1.`,
or a worked pattern's `### W1:` heading. `score` keeps each reply it scored anew (not one taken
from the memo, which an earlier round kept) with its result, the ids it cited, the start of the
hash of the text the task loaded and the Copilot files' version, in `.eval-local/sources.csv`.
A reply with no `Used:` line is "no source", never a failure; a cited id the loaded file doesn't
define is flagged. Only arm C asks for a `Used:` line, so arms A0, A1 and R keep nothing (R's
reply names the files to load, not the ids it followed).

    .venv/Scripts/python tools/eval_sources.py summary [--round <name>] [--pipeline <name>]

It ranks the cited ids by the share of failing replies that cite them against the share of
passing replies that do, so the ids most tied to failures come first, lists the failures that
cited nothing (a pattern the file lacks, or a missing line), and lists the flagged ids. The
`summary_text(rows, round_name, pipeline)` function behind it is what the cost report shows.

## The model ladder and the caps

A task costs as little as it can. `plan` with no `--model` proposes each task's model from the
ladder, haiku, then sonnet, then opus (`eval_runs.LADDER`): the cheapest model with no reply kept
under the task's key now. A task haiku failed is proposed on sonnet; one a model passed is taken
from the memo; one every model failed isn't asked again. The plan says which per task, names
the cheapest model that passed it on older text, and lists each rung's tasks: run each rung as a
round of its own, `batch ... --model <rung> --only <its tasks>`. A `--model` given overrides the
ladder for every task. The usability loop has one rung, haiku, as a larger model passing shows
nothing of the docs.

`eval_runs.CAPS` is the one table of each pipeline's cap on a proxy's reply (characters) and a
conversation's turns. Each batch writes the cap into its messages (the Metric request's into
each agent's first message). A scorer flags a reply over the cap, `OVER CAP`, in its score line
and the report, and leaves its score as it was; a Metric request conversation past its turn cap
is ended with no request, and the usability loop fails a run that asks more questions than its
cap. A plan never asks a task again whose key is unchanged, and says `from the memo` for each;
`--fresh` is the one way to ask a dev task again.

## By hand, in Copilot's web chat

1. Write the prompts and an answers file's template, which hold only the tasks `plan` says to ask:

       .venv/Scripts/python tools/copilot_eval.py prompts C --split held_out --model copilot-web > prompts-C.md
       .venv/Scripts/python tools/copilot_eval.py template C --split held_out --model copilot-web > answers-C.md

   Do the same with `A1` for the baseline. Fill in the template's header: `date:`, `arm:` (`A1`,
   `C`), `model: copilot-web`, and `files:`, the Copilot files' hash, `git rev-parse
   --short HEAD:copilot` (`none` for A1).
2. Ask Copilot, one fresh chat per task and arm, because Copilot remembers its chat:
   - **A1, before the files.** Paste the README's opening, as `copilot_eval.py batch A1 ...`
     writes it in a message file, as the first message and send it. Then send the task's prompt.
   - **C, with the file.** Paste the task's objective file (the task's heading names its
     id; `copilot_eval_tasks.py` gives its objective, `01` to `10`, `13`, `14`, `16` or `17`;
     the file is `copilot/<objective>_*.txt`) as the first message, or attach it, and send it. Then
     send the task's prompt.
   - **R, routing.** Send `copilot/00_start_here.txt`, then ask which file to load for the
     task's prompt. Write the file it names under the task's heading.
3. Paste each reply, as it came, under its task's heading in the answers file, then score the
   file:

       .venv/Scripts/python tools/copilot_eval.py score answers-C.md --split held_out

   `score` takes the answers file in place of a round's name. With `--split` or `--objective` it
   scores the round those name, taking the memo's replies for the tasks the file lacks; without
   either, only the tasks the file answers. It refuses a header with no arm or model, which
   the memo keeps each reply by.

## How an answer is scored

Each answer is scored found, parses, builds, runs and correct. A pass is correct, and also
invents no name, imports no name with `*`, adds no opt-out the task didn't need, and calls
run_query where the request asks to run it. The files help when C passes at least 20 points
more of the held-out tasks than A1.

A Workflow task, for files 13, 14, 16 and 17, asks for a Workflow notebook's cells. Every Python
block of its reply is one cell, run in order from the Workflow's folder, in a Project of its own:
its Dev and Prod Databases filled in, the Table references of the tables the task names, its
files and the cells the user ran before. Its warehouse.py sends to a warehouse of its own that
keeps each write (`tools/workflow_warehouse.py`, the Workflow journeys' too), holding the
originals the task says the user's warehouse holds, so a reply that gives every step's cell,
create, write and compare included, runs to the end. It is correct when it leaves the same
files as the reference's cells, each with the same text, under tables/, the Workflow's own
folder and references/, and its warehouse holds the same tables with the same rows.

## The Excel tasks: Copilot files 15, 11 and 12

Files 15, 11 and 12 are measured the same way, on its own tasks and scorer
(`tools/excel_eval_tasks.py`, `tools/excel_eval.py`): 124 filled-in Formula workbooks, 62 dev
and 62 held out. A proxy model reads each workbook as text; in Copilot you attach the workbook
itself. The steps above run with `excel_eval.py` in place of `copilot_eval.py`, arms `A0` and
`C`, `--tasks X01,X02,...` in place of `--objective`, and a proxy given five workbooks at most,
as a person gives one to a fresh chat: a proxy given all 62 reads its message in pieces and
cuts its replies short. Arm C loads files 15, 11 and 12, so a held-out task in arm C is asked
once per version of those three.

**The pivot tasks** (Toolbox 8.9), X85 to X124, hold PivotTables saved as Excel saves them:
X85 to X104 dev, X105 to X124 held out, written before Copilot file 20. Each case the 8.9 map
lists has a task in each split: Row and Column fields, each summary (Distinct Count in a Data
Model pivot, X100 and X119), each Show Values As, calculated fields and items, date and number
groups, totals shown or not, a Report filter, hidden items, a slicer on two pivots, a Timeline,
a value filter, GETPIVOTDATA, a default and a renamed name, and a Table, a query's Table and a
range as the source; X102 to X104 and X121 to X124 mix pivots with formulas and M, such as a
query feeding a pivot with a slicer, read back by GETPIVOTDATA (X102). A pivot task is scored
as the others are, and besides:

- **Its finals.** A pivot's own final, and one for each total level it shows,
  `<pivot> (grand total)` and `<pivot> (by <field>)`, are each correct when one query gives
  their rows, its columns in any order, a number written as text the number (a Years group's
  "2026"). A Column field is written as rows, a calculated item as a column beside the real
  rows (and added into each total its field isn't a key of, as Excel adds it), a grouped
  field's key as the label the pivot shows ("Sep", "Qtr3", "10-19"), and a Show Values As NULL
  at a total level where Excel shows a blank. A pivot a Table's GETPIVOTDATA reads is a step,
  with no final of its own. Each reference reads each step once and carries only the columns
  its final reads (ticket 17 of the 8.9 map).
- **Its Pivot filters.** Each Pivot filter is its condition, its values written in, with
  `-- Pivot filter: <kind> <field>` above it, the kind in the glossary's words (Report filter,
  hidden items, slicer, Timeline, value filter); `/* Pivot filter: ... */` after it, as the
  code path writes it, is the same mark. The query that gives a final's rows must mark
  each Pivot filter the final's reference marks, or the reply is not named: `unnamed` lists
  `Pivot filter: slicer status`.
- **Its marks.** A Column field's "written as rows", a default name's proposed
  `<sheet>_pivot`, and a calculated item added into a total ("added into the total"), are
  named in the reply's words, as any mark is.

Each pivot final's reference gives the values the pivot stored, a test holds: a Workbook check
in small, on the tasks' own workbooks.

By hand:

1. Write the held-out workbooks and the answers files:

       .venv/Scripts/python tools/excel_eval.py workbooks --split held_out --into excel-round
       .venv/Scripts/python tools/excel_eval.py template A0 --split held_out --model copilot-web > answers-excel-A0.md
       .venv/Scripts/python tools/excel_eval.py template C --split held_out --model copilot-web > answers-excel-C.md

   Fill in each header as above, with `arm: A0` or `arm: C`. A workbook whose task has a
   Power Query (each `Power Query "..."` in `excel_eval.py prompts`) has none in its file,
   since the tool can't write one: add it in Excel (Data > Get Data > Blank Query, then
   Advanced Editor), pasting the task's M. Excel can't load a query into a Table that is
   already there, so delete the typed-in Table the query loads, then Close & Load To > Table
   at A1 of its sheet, and type its formula columns again beside the loaded rows. A task
   whose text ends `Also in the workbook: a PivotTable ...` has none in its file either: add
   it with Insert > PivotTable, as the note says. A pivot task's workbook holds its
   PivotTables, slicers and Timelines, and its queries typed on a Power Query sheet, which
   Copilot reads as they are; but a Data Model pivot's (X100, X119), which Excel can't open
   without the model only Excel writes: make it by hand, with Insert > PivotTable and "Add this
   data to the Data Model" ticked, as its task's text shows it. Or build
   your own two or three workbooks with Power Query, outside the repo, and score them by
   reading the replies.
2. **A0, before the files.** In a new chat, attach the task's workbook and send
   `I attached an Excel workbook. Convert its calculations into Hive SQL.`
3. **C, with the files.** In a new chat, attach `copilot/15_*.txt`, `11_*` and `12_*` (or
   paste them, one message each), then attach the workbook and send the same request.
4. Paste each reply under its task's heading, then score each file:

       .venv/Scripts/python tools/excel_eval.py score answers-excel-C.md --split held_out

An answer passes when, once each `<...>` is filled in as you would, its Hive gives each final
Table's and pivot's rows, it says which Tables are the sources and which the finals, it names
what the task refuses, marks or leaves alone, it marks each Pivot filter, and it invents no
name. Files 15, 11 and 12 ask for no
Toolbox code: the convert Workflow writes it from the Hive, checked; a reply that has some
still has it scored apart.

## The Metric request: Copilot file 19

File 19 writes no code and works out no numbers: it asks the user about a new metric and ends
with a Metric request, the business requirements a chatbot that knows the user's databases
writes the columns from. It is measured on twenty-eight tasks (`tools/metric_eval_tasks.py`),
fifteen dev and thirteen held out, each a vague goal, the answer key the user keeps to
themselves, and a requirements key. Seven ask for what the data can't give, or gives only in
part: a column no table has, a grain the tables don't hold, a column with no definition, a
date too vague to decide. Five state a false premise, as fact, that the user's own definitions
or pasted rows refute; they pass on a request that names what refutes it and builds on the
true reading, or, where the user keeps their reading (M28), records the conflict. Held-out
tasks M18 to M23 were written after file 19 was tuned, before any was run, as were M27 and
M28. Two agents a task, each a `metric-proxy` agent (`.claude/agents/metric-proxy.md`) on
the round's model, are both given the same messy column definitions (`COLUMN_DEFINITIONS`),
part of the memo key:

- **the stand-in user**, who pasted the definitions, says the vague goal and answers from the
  key;
- **Copilot**, loaded with file 19, asks a question at a time and writes the request.

The request is scored directly, by rules, for direction rather than exactness, as the user
asked (2026-11-14): "I am more concerned with directional correctness than exact correctness.
Messy or incomplete data definitions are anticipated." Each requirement is a pattern read in
one of the request's nine parts, or one that must not be there. It is **essential** (the
source columns, or the gap named under "Missing data:" with a "Fix:"; the grain and every
condition on its rows; the column count where the user muddled it; anything a task marks) or
**helpful** (what is left out, the days, rounding, the edges). A request passes with every
essential element, more helpful elements met than not, no column name the definitions don't
give, no worked-out number ("= 50") and no SQL. An invented column or number always fails.
What refutes a false premise, and in M28 the conflict the user kept, counts wherever Copilot
said it to the user: pushing back while it asks, or in the request. The wrong reading is read
in the request alone, so pushing back and then building on the premise still fails.
Arm A0, the baseline, is Copilot given file 19's request form, the definitions and the vague
goal, with no file and no one to ask.

Run every command from the repo's root with `.venv/Scripts/python`. A round's folders, results
table, replies and ledger rows are all under `.eval-local/`, which git ignores: no record of a
round is committed. A conversation is two agents, one for each part, each spawned once with its
first message and continued with SendMessage for the turns after; the script writes every
message and reads every reply, so you only spawn and send what it prints.

1. **Plan the round.** `tools/metric_eval.py plan C --split dev --model haiku` says which tasks
   to ask and which come from the memo, with the estimate from the ledger. Ask only what can
   come out different: new tasks, or each split once after file 19 or the definitions change.
   Use `--fresh` to ask a task the memo holds, and `--over-budget` to run a round the budget
   refuses.
2. **Start it.** `tools/metric_eval.py start C --round <name> --split dev --model haiku` plans
   again, writes a folder per asked task in `.eval-local/metric/<name>/` (user.md and
   copilot.md in C, copilot.md alone in A0), and prints, per task, one line: `M01: spawn
   metric-proxy model haiku, prompt: Read <folder>/copilot.md, then write your reply to
   <folder>/turn-01-copilot.md.`
3. **Spawn what it prints.** Spawn the agent named (type `metric-proxy`, the model, the prompt
   as printed) for every task at once, and keep each task's agent id: it is that task's Copilot
   agent. Each writes its reply to the file named and ends with one word.
4. **Take the next turn.** For a task whose agent has finished, run `tools/metric_eval.py next
   <folder>`. It prints one line: spawn the user's agent (first time only: type
   `metric-proxy`, the prompt as printed, and keep its id as that task's user agent), or
   SendMessage to the Copilot or user agent you kept, with the line's text as the message. Do
   that, wait for the reply, and run `next` again. Take the tasks' turns together, a round of
   `next` lines at a time.
5. **The end.** `next` prints `ended: request in turn N` (Copilot's turn holds the Metric
   request) or `ended: turn cap, 12 turns`, and writes the folder's transcript.md and
   request.md. In A0 the one agent's first turn ends it, as `ended: no request in turn 1` where
   it holds none. Never write a turn file yourself, and
   never send an agent more than the line says: its replies come from what it was named alone.
6. **Record each agent's usage.** When a conversation has ended, take each of its two agents'
   reported total tokens and seconds, and run `tools/metric_eval.py usage <folder> --role
   copilot --tokens <tokens> --seconds <seconds> --commit <sha>`, and the same with `--role
   user` (arm C only: A0 has no user agent). That puts one ledger row per agent per conversation in `.eval-local/ledger.csv`;
   `tools/eval_runs.py ledger` prints the ledger.
7. **Score.** `tools/metric_eval.py score <name> C --split dev --model haiku` scores each
   task's request.md, a task with no folder from the memo, keeps each new request in the memo,
   and adds a row to `.eval-local/metric/results.md`. Score a round before editing file 19: a
   reply is kept under the text it is scored on.

In Copilot's web chat the same steps run by hand: paste file 19 first, then the column
definitions and the vague goal, and answer as the user would.
