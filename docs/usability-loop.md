# The usability loop: can someone with no context follow the Workflows?

Toolbox 8.2's measure of the docs (`.scratch/toolbox-8-2/map.md`, "The loop"). A fresh small
model plays a person who has never seen sqlglot Composer, given only what main ships. For a
Workflow scenario that's a technical user. For an Excel scenario it's a non-technical user who
fills in the Formula workbook, then a fresh converter who turns it into tables. Each run is
scored against its scenario's answer key. A run that passes shows the docs were enough; each
question asked shows a gap.

Run each command from the repo's top, with dev's virtual environment. Runs are made outside
the repo, in the computer's temporary folder (`<temp>/usability-loop/runs/`), so an agent finds
nothing of dev's near its work.

## Once: the agents' Python

The agents run Python from a virtual environment outside the repo, holding what a user
installs, plus openpyxl, which stands in for Excel's own hands:

    py -3.13 -m venv %TEMP%\usability-loop\python
    %TEMP%\usability-loop\python\Scripts\python -m pip install -r requirements.txt openpyxl==3.1.5

## One run

1. **Prepare the run's folder.** For scenario `W1`, run 1, today:

       .venv/Scripts/python tools/usability_loop.py prepare W1 2026-11-01-W1-1

   It builds main's tree into the folder from dev's last commit, adds the scenario's files,
   the team's connection to a warehouse that keeps each write, and, for a scenario that starts
   from a Project (W5, H2), that Project as `my_project/`, and writes each phase's message to
   `_loop/phase_<n>.md`. It prints the folder. Pass `--main <folder>` to copy a tree built
   already, for the other runs of the same round.
2. **Start phase 1's agent.** Use the `zero-context-user` agent, on Haiku, with the prompt
   `Read <run>/_loop/phase_1.md and follow it.`
3. **Answer each question it asks.** When the agent's turn ends with a `QUESTION: ` line:
   1. Run `tools/usability_loop.py route <run name> "<the question>"`. It prints the message and
      the reply file.
   2. Start a `copilot-proxy` agent, on Haiku, with: `Message file: <message>`, `Answers file:
      <reply file>`, and no header lines.
   3. Run `tools/usability_loop.py answer <run name> <n> <each file it named>`, where `<n>`
      is the question's number; the files are pasted in that order, as the Steps sheet's
      step 12 loads several. Add `--attach <path>` for each file the agent said it would
      attach, such as `my_work/report.xlsx`.
   4. Start a second, fresh `copilot-proxy` on that message and reply file.
   5. Send the reply's text back to the user agent, continuing it with its context.

   After five questions, stop the run: it is stuck.
4. **Keep each agent's last message.** Save it as `<run>/_loop/phase_<n>_reply.md`.
5. **Start the next phase, if there is one.** Start the next phase's agent the same way, fresh,
   so it remembers nothing of the one before.
6. **Score it and record it:**

       .venv/Scripts/python tools/usability_loop.py score W1 2026-11-01-W1-1 --record "<where it stopped, if it did>"

   This copies the run's folder, but for `main/` and any copy of the Toolbox's folder, into
   `.scratch/usability-loop/runs/`, and adds a row to `.scratch/usability-loop/results.md`.

## A round

- Every dev scenario runs three times, each with fresh agents.
- Every held-out scenario runs once per version of the docs.
- Fix only what a dev run showed, in what a user reads: the README, the how-tos, the Steps
  sheet, the notebooks' text, refusal messages and the Copilot files. A Toolbox bug a run
  finds is fixed too, test first.
- Then run the round again. The loop is done when every dev scenario passes three of three in
  two rounds running.

## What a user reads must be an exact process

The Copilot files, the how-tos and the Worked examples are read by people and by language
models alike. Write each fix as numbered steps in the order they are done, naming each file,
cell and call exactly, so a small model following it has nothing to guess.
