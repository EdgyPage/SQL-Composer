# Rename to sqlglot composer

Type: task
Status: resolved
Blocked by: 02
Size: L

## Question

Rename `sql_composer` to `sqlglot_composer` and "SQL Composer" to "sqlglot Composer"
everywhere: tools, tests (imports, the golden corpus file name), worked_examples, the drift
hook, the CI job's id and name, the README template, CONTEXT.md, CLAUDE.md, standards.md, the
beginner reader's brief.

## Done when

- The goldens and galleries differ only by names; the beginner reader has run.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).

## Answer

Built in the commit that resolves this ticket.

- `sql_composer/` is `sqlglot_composer/` and the product SQL Composer is sqlglot Composer,
  everywhere outside the records that keep their names: `.scratch/` (and its `sql-composer-v2`
  path), composer_core/CHANGES.md's past entries, ADRs 0001 to 0003 (0003 notes the rename),
  the GitHub repo's name in docs/agents/issue-tracker.md, and the drift hook's temp file name.
- `tests/hive_corpus/sql_composer.txt` is `sqlglot_composer.txt`; the goldens differ only in
  their header comment, and the galleries only by names. The CI job is `sqlglot-composer`.
- `named_for` now also refuses text still naming SQL Composer or sql_composer, in both
  Editions, which the swap would otherwise pass through unchanged.
- The Composer core may name sqlglot Composer, but not the sqlglot library
  (`editions.libraries_named`).
- Where a doc named the whole project "SQL Composer" (CLAUDE.md's first line, CONTEXT.md's title,
  the beginner reader's brief), it now says the Toolbox, the glossary's word for it, since
  sqlglot Composer is one Edition.
- The product name starts lower-case, as the user chose it, like the sqlglot library it uses; the
  README says "the sqlglot library" where the two sit side by side.
- The GitHub repo is still named SQL-Composer; renaming it is the user's call, and nothing in
  the Toolbox depends on it.

**Code review (2026-10-05).** Standards: fixed a refusal that read "the sqlglot sqlglot Composer
is tested on", split code spans and orphan words from reflowing, `SQL_GOLDEN`/`SQL_GALLERY` and
`SQL` names in two tests, misaligned continuation lines, the ADR note's wording. Left: long code
lines the longer name made, as E501 isn't enforced and lines over 96 already exist. Spec: added
`example_projects/` and `templates/` to the drift hook's watched folders, the old-name guard in
`named_for`, and the project-wide names above.

**Beginner reader (2026-10-05).** No leftover old name in what a user reads. Fixed: "Its Example
database" beside the sqlglot library (now "sqlglot Composer's"), and "comes from sqlglot, which
only sqlglot Composer uses" (now "the sqlglot library"). Kept: the lower-case headings and
VERSION, which are the name.

