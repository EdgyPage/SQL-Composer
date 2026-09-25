# Build the Clean-branch export

Type: task
Status: claimed
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

## Comments

**Before the first export (2026-09-25).** `main` was `3c1389881b93924867b04f6bb4e7821882d13643`,
the v1 draft. The export keeps it as the first export's parent, so it stays in `main`'s history,
and `git branch v1-draft 3c13898` gets it back as a branch.

**Build decisions (2026-09-25), where the tickets left something open.** Each picks the most
beginner-readable option; the user may overturn any of them.

- **The seams under test** are the ones ticket 13's "Export" line names: `build(source, into,
  when)`, whose output folder is checked without git; `export(repo, when)`, run in a throwaway git
  repo so the real `main` is never touched; the drift list's reading; and the hook's
  `refusal(...)`.
- **The README template is `docs/clean-branch-readme.md`.** Under `docs/`, the drift hook already
  watches it, and the pointer test now reads it. The export fills in two markers,
  `<!-- VERSION -->` and `<!-- CHEAT SHEET -->`, and refuses if either is missing. The
  template's `>>>` examples run as doctests on `dev`, so the README's first Statement can't go
  stale.
- **The stamp's comment style follows the file:** `# ...` in Python, `<!-- ... -->` in Markdown
  and HTML, since a `#` line would be a Markdown heading. Any other kind of file in
  `sql_composer/` stops the export. The README carries the stamp too, as a comment.
- **The cheat sheet** has one `### file.py` section per Toolbox file, in `__all__`'s order, with
  the file's own docstring line under it. The two constants, `TOOLBOX_VERSION` and `VERSION`,
  show their values, because their docstring is the Toolbox's own and would print the same line
  twice.
- **`_FILES`** replaces the `_FILES = None` line as a list, one file per line, `CHANGES.md`
  included.
- **The stamped copy is imported in a fresh Python** started inside the Clean tree, without
  writing `__pycache__`. That import runs the self-check with the real file list, and it also
  reads the docstrings for the cheat sheet, so the cheat sheet comes from the copy that ships.
- **How `main` is written:** the export stores the tree through its own index file, makes one
  commit whose parent is the old `main`, and moves `main` only if it still points where it did
  (update-ref with the old value). It never checks `main` out, so `dev`'s checkout and index are
  never touched, and the user's push is a plain fast-forward. The commit message is the
  `VERSION` text plus the `dev` commit it came from.
- **It also refuses** off `dev`, with uncommitted changes (so `main` gets exactly what `dev` has
  committed), and while `main` is checked out in a worktree.
- **`python tools/export_clean.py --preview <folder>`** builds the Clean tree into an empty
  folder without git or the drift check, so the README can be read before an export.
- **The hook:** only the export run alone goes through. A longer command that names the script
  used to excuse a hand commit onto `main`, and no longer does. Since the export moves `main`
  without checking it out, the hook also refuses moving `main` by hand with update-ref or a
  forced branch. Like the existing checkout rule, it reads the whole command, so a command whose
  text merely mentions such a move (a heredoc, a message) is refused too; write that text with
  the Edit tool instead.
- **`CONTEXT.md`'s Clean branch** now holds the Toolbox and its README.
