# What does `dev` enforce, and which maintainer agents does it carry?

Type: grilling
Status: open
Blocked by: 05

## Question

The user wants their principles enforced without having to repeat them. Decide:

- what `dev`'s CLAUDE.md states;
- which rules run as tests - the Clean-branch export allowlist, the Toolbox's import allowlist,
  downward-only imports between Levels, and any beginner-readability limits such as a docstring
  example on every function;
- which maintainer agents exist (a code reviewer that knows these principles, a test writer, the
  Clean-branch exporter, others) and what each one is told.

A principle that has to be repeated in prose is one a check should replace.

## Comments

**From "How does the Toolbox survive being pasted over an existing directory?" (2026-09-25).**
Checks for `dev` to carry:

- a test that every Toolbox file declares the same `TOOLBOX_VERSION`;
- the export script stamping line 1 of each file, writing the file list into `__init__.py`, and
  placing the README at `.github/README.md`;
- `main`'s allowlist is now the `sql_composer/` folder plus `.github/README.md`.
