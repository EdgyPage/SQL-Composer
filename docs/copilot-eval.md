# Scoring Copilot on the Copilot files

The Copilot files (`copilot/`) should make Microsoft Copilot write Toolbox code that works. This
is how to measure it in Copilot's web chat, against the same tasks and scorer the proxy runs
use (`tools/copilot_eval_tasks.py`, `tools/copilot_eval.py`). It reaches nothing but this
computer: you copy text into the browser and the replies back by hand.

## 1. Print the tasks

    .venv/Scripts/python tools/copilot_eval.py prompts --split held_out > prompts.md
    .venv/Scripts/python tools/copilot_eval.py template --split held_out > answers-A1.md
    .venv/Scripts/python tools/copilot_eval.py template --split held_out > answers-C.md

In each answers file, fill in its header: `arm: A1` or `arm: C`, `model: copilot-web`, and
`files:` with the Copilot files' hash, `git rev-parse --short HEAD:copilot` (`none` for A1).
Add a `date:` line too.

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

Each answer is scored found, parses, builds, runs and correct, with any invented name and any
opt-out the task didn't need; a pass is correct with neither. The files help when C passes at
least 20 points more of the held-out tasks than A1.
