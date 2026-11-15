# The usability loop: can someone with no context follow the Workflows?

Toolbox 8.2's measure of the docs (`.scratch/toolbox-8-2/map.md`, "The loop"), run by script
since the evaluation system (`.scratch/eval-system/map.md`). A fresh small model plays a person
who has never seen sqlglot Composer, given only what main ships: its README, its pages in
`main/docs/`, the Toolbox and the Copilot files, as each phase's message says. For a Workflow
scenario that is a technical user. For an Excel scenario it is a non-technical user who fills
in the Formula workbook, then a fresh converter who turns it into tables. Each run is scored
against its scenario's answer key. A run that passes shows the docs were enough; each question
asked shows a gap.

A round runs only when the user asks for one: no ticket, commit or push runs it on its own
(the user, 2026-11-14). A round gives each dev scenario one run, and each held-out scenario one
run per Toolbox version, at its raise.

These steps need no other context. Run each command from the repo's top, with dev's virtual
environment (`.venv/Scripts/python`). Nothing a round makes is committed: its records are kept
under `.eval-local/`, which git ignores, and a run's own folder is made outside the repo, in the
computer's temporary folder (`<temp>/usability-loop/runs/`), so an agent finds nothing of dev's
near its work. The loop only prints what to spawn: you spawn each agent, from the line it
prints, and record its usage.

An agent line is `<agent type> | <model> | <prompt>`: spawn that agent type, on that model,
with that prompt, exactly.

## Once: the agents' Python

The agents run Python from a virtual environment outside the repo, holding what a user
installs, plus openpyxl, which stands in for Excel's own hands:

    py -3.13 -m venv %TEMP%\usability-loop\python
    %TEMP%\usability-loop\python\Scripts\python -m pip install -r requirements.txt openpyxl==3.1.5

## Once: results kept before the memo

Runs scored before the evaluation system were recorded in `results.md` only. To bring each into
the memo, so its scenario isn't run again, run this once; running it again changes nothing:

    .venv/Scripts/python tools/usability_loop.py migrate

## A round

1. **Plan the round.** Name every scenario of the round, such as `W1 W8`:

       .venv/Scripts/python tools/usability_loop.py plan W1 W8

   It prints one line per scenario, then the round's estimate. `memoized` means every run the
   round gives the scenario (one) passed with the inputs it has now, or, for a held-out
   scenario, at the Toolbox version dev is at, and none failed: give it to no agent, and name those runs in the round's
   notes. `run it` says why: no run recorded with these inputs, fewer passed than a round asks,
   or one failed. When no run was recorded with these inputs, it also names each input that
   changed since the scenario's last recorded run, such as `changed since its last run,
   2026-11-10-W1-3: the Toolbox folder and README section "The Workflows"`. The last line is
   the round's estimated tokens, from past phase agents in the ledger (or `No estimate`, with
   none yet), and the usability budget. A round over the budget is refused: to run it anyway,
   add `--over-budget`. `--fresh` plans every run again, though each passed.
2. **Name each run.** A run is named `<date>-<scenario>-<n>`, `n` from 1 to the runs the round
   gives the scenario, one: `2026-11-14-W1-1`. The number is the run's slot in its round,
   which the memo keeps it under.
3. **Prepare the run's folder.** For scenario `W1`, run 1:

       .venv/Scripts/python tools/usability_loop.py prepare W1 2026-11-14-W1-1

   It copies in main's tree as dev's last commit builds it, the scenario's files, the team's
   connection to a warehouse that keeps each write, and, for a scenario that starts from a
   Project (W5, W8, H2), that Project as `my_project/`; writes each phase's message to
   `_loop/phase_<n>.md`, and what the run is given to `_loop/inputs.json`. It refuses a
   memoized scenario, or a slot whose run passed, naming the runs: add `--fresh` to run it
   again anyway. It prints `Run folder: <path>`, then one agent line per phase:

       zero-context-user | haiku | Read <run folder>/_loop/phase_1.md and follow it.
       zero-context-user | haiku | Read <run folder>/_loop/phase_2.md and follow it.

4. **Spawn phase 1's agent** from its line. Note the tokens and seconds Claude Code reports
   when it finishes.
5. **Record its usage**, in the ledger, from those figures; `--result` is `done`, `stuck` or
   `questions`, as its last line says:

       .venv/Scripts/python tools/usability_loop.py usage 2026-11-14-W1-1 phase-1 --tokens <tokens> --seconds <seconds> --result done

   (The round is the run's name without its slot, `2026-11-14-W1`, unless `--round <id>`
   names it.) A phase's agent
   ends its last message with a `Read: <file> <section>, ...` line, which its prompt asks for;
   add `--final "<its last message>"` to keep it in the run's `_loop/`, where `score --record`
   reads it. A run with no such line is kept as "no source", never as a failure.
6. **Answer each question it asks.** When the agent's turn ends with a `QUESTION: ` line, with
   `<n>` the question's number, counting from 1:
   1. Route it:

          .venv/Scripts/python tools/usability_loop.py route 2026-11-14-W1-1 "<the question>"

      It prints one agent line, a `copilot-proxy | haiku | Message file: ... Answers file: ...
      No header lines.` Spawn it, and record its usage with `usage 2026-11-14-W1-1 route-<n>`,
      as in step 5.
   2. Read the Answers file: it names the Copilot file or files to load next.
   3. Answer it, with each file it named, in that order, as the Steps sheet's step 12 loads
      several. Add `--attach <path>` for each file the agent said it would attach, such as
      `my_work/report.xlsx`:

          .venv/Scripts/python tools/usability_loop.py answer 2026-11-14-W1-1 <n> 07_convert_hive.txt

      It prints one agent line for a second, fresh `copilot-proxy`. Spawn it, and record its
      usage with `usage 2026-11-14-W1-1 answer-<n>`.
   4. Send the reply's text back to the user agent, continuing it with its context (a message
      to the same agent, not a new one), with: "Copilot answered your QUESTION: <the reply, or
      the file in the run's folder it was copied to>. Your run is not over: carry on with the
      job, as your phase file says, and end with one DONE:, STUCK: or QUESTION: line only when
      it is done, you are stuck, or you need Copilot again." (An agent whose turn ends by
      handing back its report reads a message after it as the end of its run and only repeats
      its report, so the message says its run is not over.) Add the tokens it reports for this
      turn to the agent's usage in step 5, or record them as a further `phase-1` row.

   After five questions, stop the run: it is stuck.
7. **Keep each agent's last message.** Save it as `<run folder>/_loop/phase_<n>_reply.md`.
8. **Run the next phase, if there is one.** Spawn the next phase's agent from its line, fresh,
   so it remembers nothing of the one before, then record its usage as `phase-2`.
9. **Score the run and record it:**

       .venv/Scripts/python tools/usability_loop.py score W1 2026-11-14-W1-1 --record "<where it stopped, if it did>"

   This copies the run's folder, but for `main/` and any copy of the Toolbox's folder, into
   `.eval-local/usability/runs/` (its phase replies and questions are the transcript), adds a
   row to `.eval-local/usability/results.md`, and keeps the run in the memo under its slot and
   inputs. It prints the score: `pass` or `FAIL`, what is missing, and the run's actions. Its
   name must end in the scenario and a number, as step 2 says.
10. **Repeat steps 3 to 9** for each run the plan said to run, each with fresh agents. Runs of
    different scenarios may be prepared at once.
11. **Read the failures.** Fix only what a dev run showed, in what a user reads: the README, the
    how-tos, the Steps sheet, the notebooks' text, refusal messages and the Copilot files. A
    Toolbox bug a run finds is fixed too, test first. Then plan the round again, and run what
    it says. The loop is done when every dev scenario passes in two rounds running. Every
    held-out scenario runs once per Toolbox version.
12. **Report.** First write the commits file, which gives the report each commit's version and
    events:

        git log --format="commit %h %cs %s" --name-only -n 600 > .eval-local/commits.txt

    Then `.venv/Scripts/python tools/eval_report.py` writes `.eval-local/report.html`: cost,
    pass rate, eventful commits and the doc ids failing runs cite.

## What the loop keeps, and where

Everything is under `.eval-local/`, which is never committed:

- `ledger.csv`: one row per agent, from `usage`: a phase's agent (role `user`, arm `phase`) or
  a question's proxy (role `proxy`, arm `question`), with its tokens, seconds and result;
- `memo/`: each scored run, under the key of its slot (the scenario and the run's number), the
  arm `run`, the model `haiku`, the hash of the scenario's text, and its inputs hash. A slot
  holding a run that failed is asked again; one holding a run that passed is not;
- `usability/runs/<run>/`: the run's folder, but for `main/` and the Toolbox's copy;
- `sources.csv`: one row per scored run (and per new reply of the other pipelines) with its
  result, its inputs hash and the files and sections its agents said they read. Read it with
  `.venv/Scripts/python tools/eval_sources.py summary [--round <id>] [--pipeline <name>]`;
  `docs/copilot-eval.md` says how it ranks them;
- `rounds.csv`: one row per scored run, passed or not, under its round, which the report
  sums into the round's pass rate beside its cost;
- `usability/results.md`: one row per scored run, its note ending `inputs <hash>`, the first
  16 characters of the run's inputs hash, which `plan` reads for what changed.

## What a run is given, and what is cached

`_loop/inputs.json` holds the scenario, dev's commit, and a SHA-256 of each thing an agent is
given, each with the export's stamp (when it ran, and from which commit) left out:

- `main`, main's tree by part:
  - `toolbox`: one hash of the Toolbox folder and the pages in main's `docs/`, whole, but for
    the how-tos on the how-to page, `docs/how_to.html`, since its code changes what every run
    does;
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
commit is left out of it. It is the text the memo's key says a run loaded. So:

- a change to the Toolbox folder or to a page in main's `docs/` runs every scenario again, but
  for a change to a how-to on the how-to page, `docs/how_to.html`, which runs again only the
  scenarios that list that how-to (a change to the page around the how-tos runs them all);
- a change to a README section, how-to or Copilot file runs again only the scenarios that list
  it; one no scenario lists runs none;
- a change to anything else of the scenario's, such as its answer key or its list, runs it
  again;
- a commit that changes none of what a scenario reads, such as one to `tools/` or `.scratch/`,
  or to a README section no scenario lists, leaves it memoized.

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

## What a user reads must be an exact process

The Copilot files, the how-tos and the Worked examples are read by people and by language
models alike. Write each fix as numbered steps in the order they are done, naming each file,
cell and call exactly, so a small model following it has nothing to guess.
