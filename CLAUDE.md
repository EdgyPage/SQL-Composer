# CLAUDE.md - dev branch

This is the **Dev branch** of the Toolbox, where all work happens. `main` is the **Clean
branch**: the Toolbox (its Templates inside it), the pages in `docs/` (the how-tos, the Example
gallery, the Workflows overview and the Example projects page, which dev writes into
`docs/main/`, and beside them the Example projects' lineage pages; main holds no Example
project and no Example database), a copy of the Copilot files (`copilot/`), its README,
`CHANGES.md`, its license (`LICENSE`, MIT No Attribution) and `requirements.txt`, each as dev
holds it, generated from this branch by `.venv/Scripts/python tools/export_clean.py` and never
edited or committed to by hand. Each export commits to `main` locally, replacing whatever it
held (before the first export, the v1 draft), and never pushes; pushing `main` is the user's
step. A hook refuses commits and file edits while `main`
is checked out.

v2 is charted and built through the wayfinder map at `.scratch/sql-composer-v2/map.md`. Read its
Notes before working any ticket. The PySpark work, which builds the Toolbox a second time without
sqlglot, is charted and built through `.scratch/spark-edition/map.md`; read its Notes too before
working one of its tickets. Toolbox 4.0 (one shared core folder, the sqlglot Composer rename,
how-tos, example projects and templates) is charted through
`.scratch/shared-core-4.0/map.md`; read its Notes before working one of its tickets. Toolbox 5.0
(Keys checked before writing, the Saved table's storage, Session settings, the Unchecked
statement, the admin module, and the joins, windows, stacking and upkeep SQL still missing) is
charted through `.scratch/toolbox-5/map.md`. Toolbox 6.0 (Spark Composer dropped, one Toolbox
folder, the README as a tutorial, and Projects: an admin folder, a notebook per Saved table, and a
flat folder of Table references feeding a Reference sheet) is charted through
`.scratch/toolbox-6/map.md`; read its Notes before working one of its tickets. Toolbox 6.1 (type
hints on every function, and Statement, Column and Condition made public) is charted through
`.scratch/toolbox-6-1/map.md`; read its Notes, which set the hint style, before working one of its
tickets. Toolbox 7.0 (query and execute in place of send, tables with no days, Databases, Python
steps, and the docs reworked into one story) is charted through `.scratch/toolbox-7/map.md`; read
its Notes before working one of its tickets. Toolbox 7.1 (`run_query` and `run_execute` in place
of `run`, so the user picks the call, and the cleanup after it) is that map's tickets
09 to 18. Toolbox 7.2 (Conversions of other people's Hive into the user's code, Upgrades that
carry a Project from one version to the next, and the version in one file) is charted through
`.scratch/toolbox-7-2/map.md`; read its Notes before working one of its tickets. Its tickets 12
to 14 add the Copilot files, `copilot/`, which `.venv/Scripts/python tools/copilot_files.py`
writes from `tools/copilot_sources/`, each at most 9,000 characters, with every file merged into
`copilot/all_in_one/all_copilot_files.txt` by `tools/merge_copilot_files.py`, and the evaluation that
measures them, `tools/copilot_eval.py`, run as `docs/copilot-eval.md` says. Its tickets 15 to 18
add Copilot file 11, which has Copilot turn a Formula workbook into Hive (ticket 20 splits it,
its Power Query and totals into file 12), and an empty
Formula workbook to copy, built on dev with `openpyxl`, which only dev installs, with filled-in
examples in `copilot/examples/` that `tools/formula_workbook_examples.py` builds; its own
evaluation, `tools/excel_eval.py`, is run as the same doc's Excel section says. Toolbox 8.0 (a
coding standard, a refactor of the Toolbox and `tools/` to it with no version raise, then
Workflows: Conversions of many scripts into the user's Dev Database, Promotion to their Prod
Database, and every Project action taking one or many) is charted through
`.scratch/toolbox-8/map.md`; read its Notes before working one of its tickets. Toolbox 8.1
(end-to-end tests of each Workflow, Decisions answered in a Workflow's notebook in place of
hand edits, a runner that runs a Workflow's steps, new tables from a query, and staging tables
folded) is charted through `.scratch/toolbox-8-1/map.md`; read its Notes before working one of
its tickets. Toolbox 8.2 (`export_hive`, each table's SQL in a file beside its notebook, and the
usability loop: zero-context agents run each Workflow and the Excel path from what main ships)
is charted through `.scratch/toolbox-8-2/map.md`; read its Notes before working one of its
tickets. Toolbox 8.3 (Script tags, `<PARM="NAME"/>` in someone else's Hive, read past by a
Conversion and answered as Decisions in the convert notebook, which keeps the user in it) is
charted through `.scratch/toolbox-8-3/map.md`; read its Notes before working one of its tickets.
Toolbox 8.4 (Run values, a function of the user's filling a Script tag's place each time a
table is written; Decisions for every table; the seed limited by Partition; the conversion
fixes the user's batch needed; and Upgrades straight from any version since 8.3) is charted
through `.scratch/toolbox-8-4/map.md`; read its Notes before working one of its tickets.
Toolbox 8.5 (fewer of the user's actions: Workflow notebooks read top to bottom, defaults in
the names cell, proposals the user accepts, `project.new_run_value`; Database settings for
dev and prod; and Building blocks copied into prod) is charted through
`.scratch/toolbox-8-5/map.md`; read its Notes before working one of its tickets.
Toolbox 8.6 (`connect` in warehouse.py, so each notebook gives its own connection; and
Scheduled runs: a notebook an outside scheduler runs, its parameters typed, building the
Statements it names with what they read in lineage order apart from running them, and the
Project's lineage drawn by hand) is charted through `.scratch/toolbox-8-6/map.md`; read its
Notes before working one of its tickets.
Toolbox 8.7 (the testing pipelines and the pytest suite memoized and run on many cores; the
lineage pages built from one page module, in bold colours, with a side panel; a Workflows
overview page; the schedule Workflow; Hivevars with defaults; Copilot file 19, the Metric
request; and the Example database out of the library, to dev only, its examples read as pages
in main's `docs/`) is charted through `.scratch/toolbox-8-7/map.md`; read its Notes before
working one of its tickets. Toolbox 8.8 (Effective logic, the Lineage state a Project records
in `admin/lineage/lineage_state.csv` each time a table or Table reference changes, and the
Lineage difference, which shows each Own and Inherited change and when it reached the data) is
charted through `.scratch/toolbox-8-8/map.md`; read its Notes before working one of its
tickets. Toolbox 8.9 (a Formula workbook converted in code by the convert Workflow, beside the
Copilot files, as two equal paths (ADR 0016); PivotTables and Pivot filters converted, Copilot
files 20 and 21; and the Workbook check, offline on the workbook's own Tables) is charted
through `.scratch/toolbox-8-9/map.md`; read its Notes before working one of its tickets. The
evaluation system (dev-only, no version: the testing pipelines on
one module, `tools/eval_runs.py`, rounds run by script, a local token ledger and cost report,
sources tied to doc ids, records kept out of git in `.eval-local/`, and the history scrubbed of
local paths) is charted through `.scratch/eval-system/map.md`; read its Notes before working one
of its tickets.

## Checks

`pytest` holds every principle a test can hold, so run `.venv/Scripts/python -m pytest`, which
tests the Toolbox and the repo's own checks, before you commit. Dev runs in a virtual
environment on Python 3.13, in `.venv` (git-ignored, and never read by the offline policy): make
it with `py -3.13 -m venv .venv`, then `.venv/Scripts/python -m pip install -r
requirements-dev.txt`, which pins what dev tests on. Run every Python command of the repo, its
tools and tests, with `.venv/Scripts/python`, never a bare `python`. `requirements.txt` is what a
user installs: the same pins, which a test holds to `requirements-dev.txt` and to the libraries
`tools/toolbox_registry.py` lets the Toolbox import.

The suite runs on pytest-xdist (Toolbox 8.7, ticket 03): `pyproject.toml`'s `-n auto --dist
loadgroup` runs the whole suite on up to 8 workers and a narrower run, such as one file, in one
process; `-n 4` or `-n 0` on the command line chooses. Tests that share a costly fixture run on
one worker, as `tests/workers.py`'s `GROUPS` says: a new costly fixture gets a line there. On
this computer the code audit and each "committed is generated" test keep a memo in
`.pytest_cache/memo/` (git-ignored) and redo only what changed; delete that folder to redo
everything. With `CI` set, as `.github/workflows/dev.yml` sets it, every generated output
regenerates whole.

CI runs one job on Python 3.13, at sqlglot's pin, which `.github/workflows/dev.yml` names: the
Toolbox's range starts at 30.19.0, and since 7.2 CI doesn't run its bottom. Export only a commit
whose CI job passed: the export doesn't check the gallery.

What no test can hold is in `docs/agents/standards.md`, which the code reviewer reads.

## Records stay local, and git holds no local path

The user: "I want good evaluation instructions to be passed around from machine to machine, the
actual records don't need to be shared at all." and "Let's make it a rule from now on not to push
that stuff." (the evaluation system, `.scratch/eval-system/map.md`).

- Git holds instructions: the tools, `docs/`, the proxy and maintainer agents, tasks with their
  keys, tests, maps and tickets. Every record stays on one machine, under the git-ignored
  `.eval-local/`: the ledger, the memo, every run folder, the results files, round summaries and
  reports. Never `git add -f` one. Every pipeline writes there itself; `.venv/Scripts/python
  tools/eval_runs.py copy-records` copies in records an older checkout left under `.scratch/`.
- A round is run by its numbered steps, with no orchestrating worker: `docs/copilot-eval.md`
  for the Copilot, Excel and Metric request evaluations, `docs/usability-loop.md` for the
  usability loop. Run only what the plan says changed. A usability round runs only when the
  user asks for one: one run a dev scenario, and a held-out scenario once a Toolbox version.
- No tracked file holds an absolute user path, the user's folder name, an AppData, Temp or
  scratchpad path, or an email. Write a path relative to the repo, or `<user folder>` and
  `<scratchpad>`. `tools/local_paths.py` is the one reader of this: `tests/repo/test_local_paths.py`
  reads every tracked file with it, the commit hook `.claude/hooks/local_paths_hook.py` refuses a
  commit that would hold one, and the export refuses a Clean tree that does. A test that names
  these patterns to check for them goes in its `NAMES_THE_PATTERNS`.

## The Toolbox's folder

The Toolbox is one folder, `sqlglot_composer/`, which writes its Hive with sqlglot (ADR 0009).
Spark Composer, a second Edition, was dropped in 6.0 (ADR 0008); the tag `last-spark-composer`
holds it. `tools/toolbox_registry.py` is the one registry of which files the folder holds and
what each may import. `CHANGES.md`, the change notes, is at the repo's top.

## A Project's admin folder

Since 8.0, a Project's admin folder, as `example_projects/intermediate/admin/` shows, keeps each
Workflow's notebook in workflows/<workflow>/, a convert batch's index beside it in
workflows/convert/<name>/ (finished/<name>/ once compared), promotion's record in
workflows/promote/promoted.json, the Dev and Prod Database settings in databases.py, and at its
top only the notebooks no one Workflow owns, such as check_project.ipynb, remove.ipynb,
lineage.ipynb and scheduled_runs.ipynb. scheduled_runs.ipynb's cells are run by hand for the
Project's Scheduled runs (8.6): each of those is a notebook in the Project's
`scheduled_runs/<name>/`, beside tables/, as
`example_projects/intermediate/scheduled_runs/weekly_team/` shows, and the Project lineage
those cells export goes in admin/lineage/. lineage.ipynb records the Lineage state by hand and
writes the Lineage difference (8.8): the state is admin/lineage/lineage_state.csv, which each
Project action that changes a table or Table reference, and each Table notebook's
`export_hive()`, add to as well.

## Drift

When a session's planned work is done, before it pushes dev, one drift review runs over every
commit the push sends that touches the Toolbox's folder, `worked_examples/`,
`example_projects/`, `copilot/`, `docs/`, `CONTEXT.md`, `CLAUDE.md`, `requirements.txt` or
`requirements-dev.txt`: it looks for anything those commits made untrue and adds one open item
per finding to `.scratch/drift.md`. It edits nothing else. No review runs after each commit or
merge.

- Fix open items as your next commits. Each fix marks its item `[x]` with the fixing commit.
- A false alarm closes with a `No-drift: <item> - <why>` line in a commit message. The reviewer
  accepts it only if the reason holds.
- Never raise the Toolbox version yourself. When a version item opens, ask the user. The
  version is written in one place, `sqlglot_composer/version.txt` (ADR 0013).
- Every version raise ships an Upgrade step, in `sqlglot_composer/upgrades.py`'s `STEPS`, even
  one with nothing to change, and freezes the Example projects as the version before left them,
  without their Lineage pages, in `tests/upgrade_from/<that version>/`; `tests/test_upgrades.py`
  fails until both are there.
- An Upgrade step never moves, renames or takes out a file in a Project's
  `scheduled_runs/<name>/`: the user's scheduler builds each run's container from its path and
  the commit (the user, 2026-11-14). It may only rewrite or mark lines inside them;
  `test_an_upgrade_keeps_every_scheduled_run_file_at_its_path` holds it.
- A hook (`.claude/hooks/drift_gate.py`) refuses `git push` from dev while a commit it sends
  has no review line or any item is open, and says what to run. For a small push of small
  commits, the user may skip the review: run `DRIFT_REVIEW=skip git push ...` only when the
  user says so; those commits stay unreviewed. The export to `main` refuses while any item is
  open.

## Offline

The Toolbox reaches nothing but the user's `query` and `execute`, and the rest of the repo
reaches only this computer, as ADR 0004 records (ADR 0012 split `send` in two);
`docs/offline-audit.md` is the audit behind it.

- `tools/offline_policy.py` is the policy reader, the one reader of that policy, and its
  `ALLOWED` lists the reviewed sites. A new entry needs a reason and the user's OK: ask before
  adding one.
- A hook, `.claude/hooks/offline_hook.py`, refuses an Edit, Write or NotebookEdit that would
  add network code; `tests/repo/test_offline_policy.py` reads the whole repo, so a file written
  any other way is caught too.
- Every test run installs a trap that refuses any lookup or connection off this computer
  (`_refuse_the_network` in `tests/offline_trap.py`).
- The export reads the Clean tree the same way before anything in it runs, and refuses on any
  finding.
- `tools/code_audit.py` reads every file for what the policy doesn't look for: hidden text,
  encoded payloads, reaches for credentials, and config that runs or fetches code. Its
  `AUDITED` lists the reviewed sites, and `tests/repo/test_code_audit.py` holds the repo clean.
  `docs/code-audit.md` (2026-10-21) is the scan behind it, of the repo, its history, `.git/`
  and `.venv`.

## Definition of done

A `task` ticket that changes code is done when:

1. `.venv/Scripts/python -m pytest` passes, and CI's job passes before the commit is
   exported;
2. the `code-review` skill has run with the ticket as its spec, and its findings are fixed or
   answered in the ticket;
3. the ticket leaves no open item in `.scratch/drift.md`;
4. if anything a beginner sees has changed (a public name, a docstring, a refusal message, the
   README template or a Worked example), the beginner reader has run and its report is linked
   from the ticket.

## Maintainer agents

- **Code reviewer:** the `code-review` skill, pointed at the ticket and
  `docs/agents/standards.md`. Spawn its two sub-agents as this repo's agents, on Sonnet for
  speed: the Standards axis as `review-standards` and the Spec axis as `review-spec`
  (`.claude/agents/`, `model: sonnet`).
- **Beginner reader:** `.claude/agents/beginner-reader.md`, on the newest Opus. It only advises;
  the user decides what changes.
- **Drift reviewer:** `.claude/hooks/drift-reviewer.md`, run as one subagent on Sonnet (model
  `sonnet`) over all the commits a push sends, as the push gate's message says (the user,
  2026-11-14: the Opus reviewer on every commit was most of the maintainers' cost).

Record each run of these agents in the ledger when it finishes, from the tokens and seconds
Claude Code reports for it (Evaluation system, ticket 08; running them is unchanged):

    .venv/Scripts/python tools/eval_runs.py record --pipeline maintainer --role maintainer --task <agent> --round <commit or ticket> --commit <commit> --arm - --model <opus or sonnet> --tokens <tokens> --seconds <seconds> --result "<clean, or opened D3 D4, or opened 2 findings>"

`<agent>` is `drift-reviewer`, `code-review-standards`, `code-review-spec` or `beginner-reader`;
`eval_runs` refuses any other, and a result that doesn't start with `clean` or `opened`. The
ledger is local (`.eval-local/`), so the data decides later whether any agent runs less often.

Each names its model by alias (`sonnet`, `opus`), which always means the newest of that class.
The skills come from `mattpocock/skills`; update them with `npx skills update -g -y`.

Tests are written with the `tdd` skill, and the glossary is kept with `domain-modeling`.

## Agent skills

### Issue tracker

Local markdown under `.scratch/<effort>/`, not GitHub Issues. See `docs/agents/issue-tracker.md`.

### Triage labels

A `Status:` line in each issue file. See `docs/agents/triage-labels.md`.

### Domain docs

Single context: `CONTEXT.md` (the glossary) and `docs/adr/` at the repo root. The skills call
the glossary GLOSSARY.md: in this repo, read and write `CONTEXT.md` wherever they say so.
