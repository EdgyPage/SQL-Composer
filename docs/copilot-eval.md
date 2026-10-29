# Scoring Copilot on the Copilot files

The Copilot files (`copilot/`) should make Microsoft Copilot write Toolbox code that works. This
is how to measure it in Copilot's web chat, against the same tasks and scorer the proxy runs
use (`tools/copilot_eval_tasks.py`, `tools/copilot_eval.py`). It reaches nothing but this
computer: you copy text into the browser and the replies back by hand.

## 1. Print the tasks

    .venv/Scripts/python tools/copilot_eval.py prompts --split held_out > prompts.md
    .venv/Scripts/python tools/copilot_eval.py template --split held_out > answers-A1.md
    .venv/Scripts/python tools/copilot_eval.py template --split held_out > answers-C.md

In each answers file, fill in its header: `date:`, `arm: A1` or `arm: C`,
`model: copilot-web`, and `files:` with the Copilot files' hash,
`git rev-parse --short HEAD:copilot` (`none` for A1).

## 2. Ask Copilot, one fresh chat per task and arm

- **A1, before the files.** Open a new chat. Paste the README's opening, as
  `.venv/Scripts/python tools/copilot_eval.py proxy A1 --split held_out` shows it between
  `<<<` and `>>>`, as the first message, and send it. Then send the task's prompt.
- **C, with the file.** Open a new chat. Paste the task's objective file (or attach it: the
  task's prompt heading names its id, and `tools/copilot_eval_tasks.py` gives its objective,
  `01` to `10`; the file is `copilot/<objective>_*.txt`) as the first message, and send it.
  Then send the task's prompt.
- **R, routing.** Open a new chat. Send `copilot/00_start_here.txt`, then ask which file to
  load for the task's prompt. Note the file it names under the task's heading.

Start a new chat for every task: Copilot remembers the chat it is in, and the tasks must not
help each other.

## 3. Paste the replies, then score them

Paste each reply, as it came, under its task's heading in the answers file. Then:

    .venv/Scripts/python tools/copilot_eval.py score answers-A1.md --record .scratch/copilot-eval/results.md
    .venv/Scripts/python tools/copilot_eval.py score answers-C.md --record .scratch/copilot-eval/results.md

Each answer is scored found, parses, builds, runs and correct. A pass is correct, and also
invents no name, imports no name with `*`, adds no opt-out the task didn't need, and calls
run_query where the request asks to run it. The files help when C passes at least 20 points
more of the held-out tasks than A1.

## The Excel tasks: Copilot file 11

File 11 is measured the same way, on its own tasks and scorer (`tools/excel_eval_tasks.py`,
`tools/excel_eval.py`): 50 filled-in Formula workbooks, 25 dev and 25 held out. A proxy model
reads each workbook as text; in Copilot you attach the workbook itself.

1. Write the held-out workbooks and the answers files:

       .venv/Scripts/python tools/excel_eval.py workbooks --split held_out --into excel-round
       .venv/Scripts/python tools/excel_eval.py template --split held_out > answers-excel-A0.md
       .venv/Scripts/python tools/excel_eval.py template --split held_out > answers-excel-C.md

   Fill in each header as above, with `arm: A0` or `arm: C`. A workbook whose task has a
   Power Query (each `Power Query "..."` in `excel_eval.py prompts`) has none in its file,
   since the tool can't write one: add it in Excel (Data > Get Data > Blank Query, then
   Advanced Editor), pasting the task's M, and Close & Load to the Table it names. A task
   whose text ends `Also in the workbook: a PivotTable ...` has none in its file either: add
   it with Insert > PivotTable, as the note says. Or build
   your own two or three workbooks with Power Query, outside the repo, and score them by
   reading the replies.
2. **A0, before the file.** In a new chat, attach the task's workbook and send
   `I attached an Excel workbook. Convert its calculations into Hive SQL.`
3. **C, with the file.** In a new chat, attach `copilot/11_*.txt`, `03_*`, `04_*` and `05_*`
   (or paste them, one message each), then attach the workbook and send the same request.
4. Paste each reply under its task's heading, then score each file:

       .venv/Scripts/python tools/excel_eval.py score answers-excel-C.md --record .scratch/copilot-eval/results.md

An answer passes when, once each `<...>` is filled in as you would, its Hive gives each final
Table's rows, it says which Tables are the sources and which the finals, it names what the
task refuses, marks or leaves alone, and it invents no name. The Toolbox code is scored apart.
