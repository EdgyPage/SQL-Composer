# Scoring Copilot on the Copilot files

The Copilot files (`copilot/`) should make Microsoft Copilot write Toolbox code that works. This
is how to measure it in Copilot's web chat, against the same tasks and scorer the proxy runs
use (`tools/copilot_eval_tasks.py`, `tools/copilot_eval.py`). It reaches nothing but this
computer: you copy text into the browser and the replies back by hand.

## The memo: ask only what changed

Every reply is kept, with its score, in `.scratch/copilot-eval/memo/` (`tools/eval_memo.py`),
one plain file per key, so a round asks a model only the tasks whose text changed. A reply's
key is:

- the task's id and text, the prompt it is asked;
- the arm;
- the model, `copilot-web` for Copilot's web chat;
- the text the arm loads before the prompt: nothing in A0, the README's opening in A1, the
  task's objective file in C, and in R file 00 and the file the reply names;
- for a held-out task in an arm that loads a Copilot file (C and R, and the Excel tasks' C),
  the Copilot files' version too: one hash of every file in `copilot/`.

A held-out task is asked once per files version: the memo never scores it against a version it
wasn't asked on, and `--fresh` doesn't ask it again on the same one. In A0 and A1, which load no
Copilot file, a held-out task is asked once until its text or the arm's text changes. Each memo
file holds its key, the date it was asked, its score line, then the reply as it came.

Before a round, see what it asks:

    .venv/Scripts/python tools/copilot_eval.py plan C --split dev --objective 03 --model haiku

`plan` first prints the Copilot files' version, then says of each task `ask:` and why (no reply
kept, its text changed, the text its arm loads changed, or held out and the Copilot files
changed), or `from the memo` and the file. `--fresh` asks every dev task again. `prompts`,
`proxy` and `template` take the same arm, `--split`, `--objective`, `--model` and `--fresh`,
and write only the tasks `plan` says to ask; when it says none, they print `Nothing to ask`.

Every answers file's header holds `memo_files:`, the files version its replies were asked on:
`template` writes it, and for a proxy round you write the one `plan` printed. `score` keeps a
held-out reply, and takes the round's kept held-out replies, by that version, not by the files
as they are when you score, and refuses a held-out reply whose header has none.

## 1. Print the tasks

    .venv/Scripts/python tools/copilot_eval.py prompts --arm C --split held_out --model copilot-web > prompts-C.md
    .venv/Scripts/python tools/copilot_eval.py template --arm A1 --split held_out --model copilot-web > answers-A1.md
    .venv/Scripts/python tools/copilot_eval.py template --arm C --split held_out --model copilot-web > answers-C.md

Print `prompts-A1.md` the same way with `--arm A1`. In each answers file, fill in its header:
`date:`, `arm: A1` or `arm: C`, `model: copilot-web`, and `files:` with the Copilot files'
hash, `git rev-parse --short HEAD:copilot` (`none` for A1). Leave `memo_files:` as `template`
wrote it.

## 2. Ask Copilot, one fresh chat per task and arm

- **A1, before the files.** Open a new chat. Paste the README's opening, as
  `.venv/Scripts/python tools/copilot_eval.py proxy A1 --split held_out` shows it between
  `<<<` and `>>>`, as the first message, and send it. Then send the task's prompt.
- **C, with the file.** Open a new chat. Paste the task's objective file (or attach it: the
  task's prompt heading names its id, and `tools/copilot_eval_tasks.py` gives its objective,
  `01` to `10`, `13`, `14` or `16`; the file is `copilot/<objective>_*.txt`) as the first message,
  and send it. Then send the task's prompt.
- **R, routing.** Open a new chat. Send `copilot/00_start_here.txt`, then ask which file to
  load for the task's prompt. Note the file it names under the task's heading.

Start a new chat for every task: Copilot remembers the chat it is in, and the tasks must not
help each other.

## 3. Paste the replies, then score them

Paste each reply, as it came, under its task's heading in the answers file. Then score each
file with the round's `--split` (and `--objective`, where the round had one):

    .venv/Scripts/python tools/copilot_eval.py score answers-A1.md --split held_out --record .scratch/copilot-eval/results.md
    .venv/Scripts/python tools/copilot_eval.py score answers-C.md --split held_out --record .scratch/copilot-eval/results.md

`score` scores the answers file's replies and, for every other task of the round, the reply
the memo keeps under its key now, and keeps each with its new score. It refuses a file whose
header doesn't give its arm and model, which the memo keeps each reply by, or a held-out reply
with no `memo_files:`. Its report and its
row of `results.md`, in the last column, say how many replies came from the memo. Without
`--split` or `--objective` it scores the file's replies alone, and still keeps them.

Each answer is scored found, parses, builds, runs and correct. A pass is correct, and also
invents no name, imports no name with `*`, adds no opt-out the task didn't need, and calls
run_query where the request asks to run it. The files help when C passes at least 20 points
more of the held-out tasks than A1.

A Workflow task, for files 13, 14 and 16, asks for a Workflow notebook's cells. Every Python block
of its reply is one cell, run in order from the Workflow's folder, in a Project of its own:
its Dev and Prod Databases filled in, the Table references of the tables the task names, its
files and the cells the user ran before. Its warehouse.py sends to a warehouse of its own that
keeps each write (`tools/workflow_warehouse.py`, the Workflow journeys' too), holding the
originals the task says the user's warehouse holds, so a reply that gives every step's cell,
create, write and compare included, runs to the end. It is correct when it leaves the same
files as the reference's cells, each with the same text, under tables/, the Workflow's own
folder and references/, and its warehouse holds the same tables with the same rows.

## The Excel tasks: Copilot files 15, 11 and 12

Files 15, 11 and 12 are measured the same way, on its own tasks and scorer (`tools/excel_eval_tasks.py`,
`tools/excel_eval.py`): 84 filled-in Formula workbooks, 42 dev and 42 held out. A proxy model
reads each workbook as text; in Copilot you attach the workbook itself.

They keep their replies in the same memo, keyed the same way: the text arm C loads is files
15, 11 and 12, and a held-out task in arm C is asked once per files version. `plan`,
`prompts`, `proxy`, `template` and `score` take the round's tasks by `--split` and `--tasks`
in place of `--objective`:

    .venv/Scripts/python tools/excel_eval.py plan C --split dev --tasks X01,X02,X03,X04,X05 --model haiku

1. Write the held-out workbooks and the answers files:

       .venv/Scripts/python tools/excel_eval.py workbooks --split held_out --into excel-round
       .venv/Scripts/python tools/excel_eval.py template --arm A0 --split held_out --model copilot-web > answers-excel-A0.md
       .venv/Scripts/python tools/excel_eval.py template --arm C --split held_out --model copilot-web > answers-excel-C.md

   Fill in each header as above, with `arm: A0` or `arm: C`. A workbook whose task has a
   Power Query (each `Power Query "..."` in `excel_eval.py prompts`) has none in its file,
   since the tool can't write one: add it in Excel (Data > Get Data > Blank Query, then
   Advanced Editor), pasting the task's M. Excel can't load a query into a Table that is
   already there, so delete the typed-in Table the query loads, then Close & Load To > Table
   at A1 of its sheet, and type its formula columns again beside the loaded rows. A task
   whose text ends `Also in the workbook: a PivotTable ...` has none in its file either: add
   it with Insert > PivotTable, as the note says. Or build
   your own two or three workbooks with Power Query, outside the repo, and score them by
   reading the replies.
2. **A0, before the files.** In a new chat, attach the task's workbook and send
   `I attached an Excel workbook. Convert its calculations into Hive SQL.`
3. **C, with the files.** In a new chat, attach `copilot/15_*.txt`, `11_*` and `12_*` (or
   paste them, one message each), then attach the workbook and send the same request.
4. Paste each reply under its task's heading, then score each file:

       .venv/Scripts/python tools/excel_eval.py score answers-excel-C.md --split held_out --record .scratch/copilot-eval/results.md

A proxy round gives each proxy model a few workbooks, as a person gives one to a fresh
chat: `excel_eval.py proxy C --split dev --tasks X01,X02,X03,X04,X05 --model haiku`, one
message per five tasks the plan names, each answered by its own proxy, the replies merged
under one header to score with the round's `--split` and `--tasks`.
Given all 42 at once, a proxy reads its message in pieces and cuts its replies short.

An answer passes when, once each `<...>` is filled in as you would, its Hive gives each final
Table's rows, it says which Tables are the sources and which the finals, it names what the
task refuses, marks or leaves alone, and it invents no name. Files 15, 11 and 12 ask for no
Toolbox code: the convert Workflow writes it from the Hive, checked; a reply that has some
still has it scored apart.

## The Metric request: Copilot file 19

File 19 writes no code: it asks the user about a new metric and ends with a Metric request,
which a chatbot that knows the user's databases defines the columns from. It is measured on
six tasks (`tools/metric_eval_tasks.py`), four dev and two held out, each a vague goal and the
answer key the user keeps to themselves, by `tools/metric_eval.py` and three proxies a task,
each a `metric-proxy` agent (`.claude/agents/metric-proxy.md`) on the round's model, or, in a
session that can't spawn it yet, a `copilot-proxy` told its part is in its message file:

- **the stand-in user** says the vague goal and answers from the key;
- **Copilot**, loaded with file 19, asks a question at a time and writes the request;
- **the stand-in chatbot**, given only the Example database's column descriptions and the
  request, writes the column as one Hive SELECT.

The column passes when its Hive gives the key's numbers on the Example database, whatever its
columns are called; in arm C the request must also be there and hold no SQL. Arm A0, the
baseline, is the same chatbot given the vague goal alone. The thresholds are in
`.scratch/copilot-eval/results.md`'s Metric request section.

1. **Plan, then write the messages.** `metric_eval.py plan C --split dev --model haiku` says
   which tasks to ask, as the memo keeps them; `messages C ... --into <run>` writes a folder
   per task: user.md and copilot.md in C, chatbot-message.md in A0.
2. **Grill.** Spawn a proxy for each part. Copilot reads copilot.md and writes
   turn-01-copilot.md; the user reads user.md and that turn, and writes turn-01-user.md; and
   so on, each continued with the other's newest turn, until Copilot's turn holds the Metric
   request, or after 12 of Copilot's turns.
3. **The chatbot.** `metric_eval.py chatbot <run>/M01` writes the folder's transcript.md,
   request.md and chatbot-message.md. A chatbot proxy reads chatbot-message.md and writes
   chatbot.md. In A0 this is the only step.
4. **Score.** `metric_eval.py answers <run> --arm C --model haiku --files <hash> --memo-files
   <version> --into <run>/answers.md` gathers the folders, `--memo-files` the version `plan`
   printed; then `score <run>/answers.md --split dev --record .scratch/copilot-eval/results.md`.

In Copilot's web chat the same steps run by hand: paste file 19 first, then the vague goal,
and answer as the user would.
