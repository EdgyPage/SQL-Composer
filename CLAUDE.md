# CLAUDE.md - dev branch

This is the **Dev branch** of the Toolbox, where all work happens. `main` is the **Clean
branch**: the Toolbox, each Edition's copy of the Example projects and the Templates, and
its README, generated from this branch by `python tools/export_clean.py` and never edited or committed to by hand. Each export commits to
`main` locally, replacing whatever it held (before the first export, the v1 draft), and never
pushes; pushing `main` is the user's step. A hook refuses commits and file edits while `main`
is checked out.

v2 is charted and built through the wayfinder map at `.scratch/sql-composer-v2/map.md`. Read its
Notes before working any ticket. The PySpark work, which builds the Toolbox a second time without
sqlglot, is charted and built through `.scratch/spark-edition/map.md`; read its Notes too before
working one of its tickets. Toolbox 4.0 (one shared core folder, the sqlglot Composer rename,
how-tos, example projects and templates) is charted through
`.scratch/shared-core-4.0/map.md`; read its Notes before working one of its tickets.

## Checks

`pytest` holds every principle a test can hold, so run both runs before you commit:
`python -m pytest`, which tests sqlglot Composer and the repo's own checks, and
`python -m pytest --edition spark`, which tests Spark Composer. Spark Composer's Example database
needs Java 17: without it, its tests skip and say so. Set up with
`pip install -r requirements-dev.txt`.

CI runs four jobs on Python 3.11: each Edition at the bottom of its library's range and at its
pin, which `.github/workflows/dev.yml` names. Spark Composer's jobs run on Java 17, with sqlglot
uninstalled and `--example-database required`, so a Spark test that can't run fails rather
than skips. Export only a commit whose four jobs passed: the export checks neither gallery, and
Spark Composer's needs Java to check.

What no test can hold is in `docs/agents/standards.md`, which the code reviewer reads.

## Two Editions

The Toolbox is built twice, as ADR 0002 records: `sqlglot_composer/` (sqlglot Composer, which
writes its Hive with sqlglot) and `spark_composer/` (Spark Composer, which prints its own Hive
and runs it on Spark). Both run the Composer core, `composer_core/`, which holds every file they
share, once, as ADR 0003 records. `tools/editions.py` is the one registry of which files the
core holds and which each Edition writes itself.

- Edit a shared file in `composer_core/`. Its docstrings name sqlglot Composer; Spark Composer's
  gallery and doctests read them with the names swapped.
- `sqlglot_composer/writing.py` and `sqlglot_composer/engine.py` are written by hand, and so are
  `spark_composer/writing.py` and `spark_composer/engine.py`, with the same function names and
  parameters, which a test holds. `sqlglot_composer/__init__.py` and
  `spark_composer/__init__.py` are the same apart from the names, which a test holds too.
- A Python runs one Edition: a test that needs the other loads its file by path, or runs it in a
  Python of its own.

## Drift

After a commit that touches the Composer core or either Edition of the Toolbox,
`worked_examples/`, `docs/`, `CONTEXT.md`, `CLAUDE.md` or `requirements-dev.txt`, the drift
reviewer looks for anything the commit made untrue and adds one open item per finding to
`.scratch/drift.md`. It edits nothing else.

- Fix open items as your next commits. Each fix marks its item `[x]` with the fixing commit.
- A false alarm closes with a `No-drift: <item> - <why>` line in a commit message. The reviewer
  accepts it only if the reason holds.
- Never raise the Toolbox version yourself. When a version item opens, ask the user.
- A stop hook blocks the first try to end a turn while your own commits have an unrun review or
  an open item, then lets a second try through so you can ask the user. The export to `main`
  refuses while any item is open.

## Offline

The Toolbox reaches nothing but the user's `send`, and the rest of the repo reaches only this
computer, as ADR 0004 records; `docs/offline-audit.md` is the audit behind it.

- `tools/offline_policy.py` is the policy reader, the one reader of that policy, and its
  `ALLOWED` lists the reviewed sites. A new entry needs a reason and the user's OK: ask before
  adding one.
- A hook, `.claude/hooks/offline_guard.py`, refuses an Edit, Write or NotebookEdit that would
  add network code; `tests/repo/test_offline_policy.py` reads the whole repo, so a file written
  any other way is caught too.
- The Example database's own Spark process runs under a trap that refuses any lookup or
  connection off this computer (`_refuse_the_network` in `spark_composer/engine.py`), and
  every test run installs the same trap (`tests/offline_trap.py`).
- The export reads the Clean tree the same way before anything in it runs, and refuses on any
  finding.

## Definition of done

A `task` ticket that changes code is done when:

1. both runs pass, `python -m pytest` and `python -m pytest --edition spark`, and CI's four
   jobs pass before the commit is exported;
2. the `code-review` skill has run with the ticket as its spec, and its findings are fixed or
   answered in the ticket;
3. the ticket leaves no open item in `.scratch/drift.md`;
4. if anything a beginner sees has changed (a public name, a docstring, a refusal message, the
   README template or a Worked example), the beginner reader has run and its report is linked
   from the ticket.

## Maintainer agents

- **Code reviewer:** the `code-review` skill, pointed at the ticket and
  `docs/agents/standards.md`.
- **Beginner reader:** `.claude/agents/beginner-reader.md`. It only advises; the user decides
  what changes.

Tests are written with the `tdd` skill, and the glossary is kept with `domain-modeling`.

## Agent skills

### Issue tracker

Local markdown under `.scratch/<effort>/`, not GitHub Issues. See `docs/agents/issue-tracker.md`.

### Triage labels

A `Status:` line in each issue file. See `docs/agents/triage-labels.md`.

### Domain docs

Single context: `CONTEXT.md` (the glossary) and `docs/adr/` at the repo root.
