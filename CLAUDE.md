# CLAUDE.md - dev branch

This is the **Dev branch** of the Toolbox, where all work happens. `main` is the **Clean
branch**: the Toolbox (its Templates inside it), a copy of the Example projects and of the
Copilot files (`copilot/`), its README,
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
writes from `tools/copilot_sources/`, each at most 8,000 characters, with every file merged into
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
`.scratch/toolbox-8/map.md`; read its Notes before working one of its tickets.

## Checks

`pytest` holds every principle a test can hold, so run `.venv/Scripts/python -m pytest`, which
tests the Toolbox and the repo's own checks, before you commit. Dev runs in a virtual
environment on Python 3.12, in `.venv` (git-ignored, and never read by the offline policy): make
it with `py -3.12 -m venv .venv`, then `.venv/Scripts/python -m pip install -r
requirements-dev.txt`, which pins what dev tests on. Run every Python command of the repo, its
tools and tests, with `.venv/Scripts/python`, never a bare `python`. `requirements.txt` is what a
user installs: the same pins, which a test holds to `requirements-dev.txt` and to the libraries
`tools/toolbox_registry.py` lets the Toolbox import.

CI runs one job on Python 3.12, at sqlglot's pin, which `.github/workflows/dev.yml` names: the
Toolbox's range starts at 30.19.0, and since 7.2 CI doesn't run its bottom. Export only a commit
whose CI job passed: the export doesn't check the gallery.

What no test can hold is in `docs/agents/standards.md`, which the code reviewer reads.

## The Toolbox's folder

The Toolbox is one folder, `sqlglot_composer/`, which writes its Hive with sqlglot (ADR 0009).
Spark Composer, a second Edition, was dropped in 6.0 (ADR 0008); the tag `last-spark-composer`
holds it. `tools/toolbox_registry.py` is the one registry of which files the folder holds and
what each may import. `CHANGES.md`, the change notes, is at the repo's top.

## A Project's admin folder

Since 8.0, a Project's admin folder, as `example_projects/intermediate/admin/` shows, keeps each
Workflow's notebook in workflows/<workflow>/, a convert batch's index beside it in
workflows/convert/<name>/ (finished/<name>/ once compared), promotion's record in
workflows/promote/promoted.json, the Dev and Prod Database names in databases.py, and at its
top only the notebooks no one Workflow owns, such as check_project.ipynb and remove.ipynb.

## Drift

After a commit that touches the Toolbox's folder, `worked_examples/`, `example_projects/`,
`copilot/`, `docs/`, `CONTEXT.md`, `CLAUDE.md`, `requirements.txt` or `requirements-dev.txt`, the
drift reviewer looks for anything the commit made untrue and adds one open item per finding to
`.scratch/drift.md`. It edits nothing else.

- Fix open items as your next commits. Each fix marks its item `[x]` with the fixing commit.
- A false alarm closes with a `No-drift: <item> - <why>` line in a commit message. The reviewer
  accepts it only if the reason holds.
- Never raise the Toolbox version yourself. When a version item opens, ask the user. The
  version is written in one place, `sqlglot_composer/version.txt` (ADR 0013).
- Every version raise ships an Upgrade step, in `sqlglot_composer/upgrades.py`'s `STEPS`, even
  one with nothing to change, and freezes the Example projects as the version before left them,
  without their Lineage pages, in `tests/upgrade_from/<that version>/`; `tests/test_upgrades.py`
  fails until both are there.
- A stop hook blocks the first try to end a turn while your own commits have an unrun review or
  an open item, then lets a second try through so you can ask the user. The export to `main`
  refuses while any item is open.

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
- **Drift reviewer:** `.claude/hooks/drift-reviewer.md`, run as a subagent on the newest Opus
  (model `opus`), as the drift hook's message says.

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
