# CLAUDE.md - dev branch

This is the **Dev branch** of SQL Composer, where all work happens. `main` is the **Clean
branch**: the Toolbox and its README, generated from this branch by
`python tools/export_clean.py` and never edited or committed to by hand. Each export commits to
`main` locally, replacing whatever it held (before the first export, the v1 draft), and never
pushes; pushing `main` is the user's step. A hook refuses commits and file edits while `main`
is checked out.

v2 is charted and built through the wayfinder map at `.scratch/sql-composer-v2/map.md`. Read its
Notes before working any ticket. The PySpark work, which builds the Toolbox a second time without
sqlglot, is charted and built through `.scratch/spark-edition/map.md`; read its Notes too before
working one of its tickets.

## Checks

`pytest` holds every principle a test can hold, so run `python -m pytest` before you commit. CI
runs it on Python 3.11 at both ends of the supported sqlglot range. Set up with
`pip install -r requirements-dev.txt`.

What no test can hold is in `docs/agents/standards.md`, which the code reviewer reads.

## Two Editions

The Toolbox is built twice, as ADR 0002 records: `sql_composer/` (SQL Composer, which writes its
Hive with sqlglot) and `spark_composer/` (Spark Composer, which prints its own Hive and runs it on
Spark). `tools/editions.py` is the one registry of which files the two share and which each writes
itself.

- Edit a shared file only in `sql_composer/`, then run `python tools/make_spark_edition.py`. Never
  edit a generated copy in `spark_composer/`: a test fails while one is stale, and names that
  command.
- `sql_composer/writing.py` and `sql_composer/engine.py` are written by hand, and so are
  `spark_composer/writing.py` and `spark_composer/engine.py`, with the same function names and
  parameters, which a test holds.

## Drift

After a commit that touches either Edition of the Toolbox, `worked_examples/`, `docs/`,
`CONTEXT.md`, `CLAUDE.md` or `requirements-dev.txt`, the drift reviewer looks for anything the
commit made untrue and adds one open item per finding to `.scratch/drift.md`. It edits nothing
else.

- Fix open items as your next commits. Each fix marks its item `[x]` with the fixing commit.
- A false alarm closes with a `No-drift: <item> - <why>` line in a commit message. The reviewer
  accepts it only if the reason holds.
- Never raise the Toolbox version yourself. When a version item opens, ask the user.
- A stop hook blocks the first try to end a turn while your own commits have an unrun review or
  an open item, then lets a second try through so you can ask the user. The export to `main`
  refuses while any item is open.

## Definition of done

A `task` ticket that changes code is done when:

1. `pytest` passes;
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
