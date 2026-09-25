# Build the Clean-branch export

Type: task
Status: open
Blocked by: 18

## Question

Build `tools/export_clean.py` and its `dev` test, as decided in "What does `dev` enforce, and
which maintainer agents does it carry?". Replace `main`'s v1 with the first Clean branch.

The governing decisions, each in its own ticket:

- **"How does the Toolbox survive being pasted over an existing directory?":** stamp line 1 of
  every Toolbox file, write the file list into `__init__.py`, and put the README at
  `.github/README.md`. `main`'s allowlist is the `sql_composer/` folder plus `.github/README.md`.
- **"What's in the Toolbox?":** the README's cheat sheet is one line per public name, grouped by
  module, built from each docstring's first line.
- **"What does `dev` enforce, and which maintainer agents does it carry?":**
  - the script builds in a temporary folder;
  - it imports the stamped copy and checks the allowlist;
  - it commits to `main` locally, and the user pushes;
  - it refuses while `.scratch/drift.md` has an open item;
  - the hook protecting `main` lets this script through;
  - the `dev` test runs the same build without git.

Done when the `dev` checks pass, the export has run once, and `main` holds only the allowlist.
Pushing `main` is the user's step.
