# CLAUDE.md - dev branch

This is the **Dev branch** of SQL Composer. `main` is the **Clean branch**: it is generated from
this branch by an export script and is never edited or committed to by hand. Until that export
exists, `main` still holds the v1 draft - leave it alone.

v2 is being charted and built through the wayfinder map at `.scratch/sql-composer-v2/map.md`.
Read its Notes before working any ticket. The v1 code in this tree is a superseded first draft;
do not build on it or on its vocabulary.

The rest of this file - the principles, checks and maintainer agents - is decided by the ticket
"What does `dev` enforce, and which maintainer agents does it carry?".

## Agent skills

### Issue tracker

Local markdown under `.scratch/<effort>/`, not GitHub Issues. See `docs/agents/issue-tracker.md`.

### Triage labels

A `Status:` line in each issue file. See `docs/agents/triage-labels.md`.

### Domain docs

Single context: `CONTEXT.md` (the glossary) and `docs/adr/` at the repo root.
