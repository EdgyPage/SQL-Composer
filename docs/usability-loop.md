# The usability loop: can someone with no context follow the Workflows?

Toolbox 8.2's measure of the docs (`.scratch/toolbox-8-2/map.md`, "The loop"). A fresh small
model plays a person who has never seen sqlglot Composer, given only what main ships: its
README, its pages in `main/docs/` (the how-tos, the Example gallery, the Workflows overview and
the Example projects, since Toolbox 8.7's ticket 13 took them out of the Toolbox's folder and
main's `example_projects/` away), the Toolbox and the Copilot files, as each phase's message
says. For a
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

## First: which scenarios to run

    .venv/Scripts/python tools/usability_loop.py plan W1 W8

`plan` prints one line per scenario. `memoized` means the runs a round gives it (three for a
dev scenario, one for a held-out one) passed with the inputs it has now, and none failed: give
it to no agent, and name those runs in the round's notes. `run it` says why: no run recorded
with these inputs, fewer passed than a round asks, or one failed. When no run was recorded with
these inputs, it also names each input that changed since the scenario's last recorded run,
such as `changed since its last run, 2026-11-10-W1-3: the Toolbox folder and README section
"The Workflows"`. The inputs are what an agent is given and reads (see "What a run is given",
below), not dev's commit, so a commit that changes none of them, such as one to `tools/` or
`.scratch/`, or to a README section no scenario lists, leaves a scenario memoized.

## One run

1. **Prepare the run's folder.** For scenario `W1`, run 1, today:

       .venv/Scripts/python tools/usability_loop.py prepare W1 2026-11-01-W1-1

   It copies in main's tree as dev's last commit builds it, the scenario's files, the team's
   connection to a warehouse that keeps each write, and, for a scenario that starts from a
   Project (W5, W8, H2), that Project as `my_project/`; writes each phase's message to
   `_loop/phase_<n>.md`, and what the run is given to `_loop/inputs.json`. It prints the
   folder. It refuses a memoized scenario, naming its runs: add `--fresh` to run it again
   anyway.
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
   5. Send the reply's text back to the user agent, continuing it with its context. An agent
      whose turn ends by handing back its report reads a message after it as the end of its
      run and only repeats its report (three of the 8.7 round's ten Excel converters did),
      so say in the same message that its run is not over: "Copilot answered your QUESTION:
      <the reply, or the file in the run's folder it was copied to>. Your run is not over:
      carry on with the job, as your phase file says, and end with one DONE:, STUCK: or
      QUESTION: line only when it is done, you are stuck, or you need Copilot again."

   After five questions, stop the run: it is stuck.
4. **Keep each agent's last message.** Save it as `<run>/_loop/phase_<n>_reply.md`.
5. **Start the next phase, if there is one.** Start the next phase's agent the same way, fresh,
   so it remembers nothing of the one before.
6. **Score it and record it:**

       .venv/Scripts/python tools/usability_loop.py score W1 2026-11-01-W1-1 --record "<where it stopped, if it did>"

   This copies the run's folder, but for `main/` and any copy of the Toolbox's folder, into
   `.scratch/usability-loop/runs/`, and adds a row to `.scratch/usability-loop/results.md`.
   The row's note ends `inputs <hash>`, the first 16 characters of the run's inputs hash:
   `plan` reads it there, so keep it when you move the row into the round's section.

## What a run is given, and what is cached

`_loop/inputs.json` holds the scenario, dev's commit, and a SHA-256 of each thing an agent is
given, each with the export's stamp (when it ran, and from which commit) left out:

- `main`, main's tree by part:
  - `toolbox`: one hash of the Toolbox folder and the pages in main's `docs/` (since Toolbox
    8.7's ticket 13 moved them out of the folder), whole, but for the how-tos on the how-to
    page, `docs/how_to.html`, since its code changes what every run does;
  - `readme`: the README, one hash per `##` section, by its heading, the part above the first
    by the README's title, `sqlglot Composer`;
  - `how_tos`: each how-to of `docs/how_to.html`, by its link, such as
    `convert_someone_elses_hive`;
  - `copilot`: each Copilot file, by its path from `copilot/`;
  - `named`: each other file of main the phases' messages name, such as
    `copilot/formula_workbook.xlsx`, on its own; the README every message names is hashed by
    section instead;
- `reads`: what the scenario's path reads of main, from its `reads.json`, beside its answer
  key: the README sections, by heading, the how-tos and the Copilot files;
- `project`: each file of the Project the user starts from, as it is brought in, before its
  connection is filled in, but for its copy of the Toolbox, which is main's;
- `warehouse`: the team's warehouse, as the scenario's Hive left it;
- `scenario_files`: each file of the scenario's folder, its answer key among them;
- `phases`: each phase's message, as written for no run in particular;
- `loop_files`: the runner, the warehouse's code and the team's connection the loop puts in,
  and the lines it gives a Project brought in that connection by, each hashed on its own.

`inputs_hash` is made only from what the scenario's agents read: the Toolbox folder, the parts
of main its `reads.json` lists, the files the phases name, the rest of `inputs.json`
(`project`, `warehouse`, `scenario_files`, `phases`, `loop_files`) and the list itself; dev's
commit is left out of it. So:

- a change to the Toolbox folder or to a page in main's `docs/` runs every scenario again, but
  for a change to a how-to on the how-to page, `docs/how_to.html`, which runs again only the
  scenarios that list that how-to (a change to the page around the how-tos runs them all);
- a change to a README section, how-to or Copilot file runs again only the scenarios that list
  it; one no scenario lists runs none;
- a change to anything else of the scenario's, such as its answer key or its list, runs it
  again.

`prepare` and `plan` refuse a scenario whose list names a section, how-to or Copilot file main
hasn't, so one renamed can't leave a scenario memoized on nothing; a test holds every list to
main too. Each list is written by `tools/usability_scenario_files.py`, with the rest of the
scenario's folder: change it there, then build the scenarios again.

Runs recorded before Toolbox 8.7 name a hash made with one hash of main's whole tree, which no
run's hash is now, so `plan` says to run each of those scenarios once more, and never reads
those runs as memoized.

Two things are cached, in `%TEMP%\usability-loop\cache\`, so a round builds each once:

- `main\<commit>\`: main's tree, built once per dev commit by the export's own builder, then
  copied into each run;
- `scenarios\<commit>\<scenario>-<hash>\`: each scenario's files, its warehouse having run its
  Hive, and any Project its user starts from (for W5, the end of W2), set up once per dev
  commit and scenario, then copied into each run. The hash is that of what the set-up is made
  from: the scenario's own files, the folder of dev's its Project is copied from (such as
  `example_projects/intermediate` for W8), and the files of the scenario it starts from (W2's,
  for W5), so an edit to any of them, committed or not, sets it up again.

Building a new commit's tree removes every other commit's cache. To clear it all, delete the
folder: `rmdir /s /q %TEMP%\usability-loop\cache`. Nothing in it is ever edited: a run works
on its own copy.

Prepares may run at once, such as one per agent of a round. Each builds into a folder of its
own and renames it into place, so no prepare takes a half-built tree, or removes another's.
While a prepare (or a `plan`) builds, drops or copies from the cache, it holds the cache's lock,
the folder `cache\prepare.lock`, and removes it when it is done, however it ends:

- If another prepare holds the lock, this one waits for it, up to five minutes.
- If the lock is still held after that, the prepare stops and names the lock folder. If a
  prepare is still running, wait for it to finish, then prepare again. If none is running, one
  was stopped while it held the lock: delete `cache\prepare.lock`, then prepare again.

## A round

- First run `plan` on every scenario of the round, and give agents only those it says to run.
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
