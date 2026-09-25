# Build the Clean-branch export

Type: task
Status: resolved
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

**Code review (2026-09-25), `code-review` over `78b9cc7..HEAD`,** with this ticket and tickets 05,
12 and 13 as the spec and `docs/agents/standards.md` as the standards. Fixed in `fd622bc`:

- **Spec:**
  - A drift list without its `## Items` heading read as having no open items. It now stops the
    export.
  - The build read the checkout, so a file git ignores in `sql_composer/` could ship. It now reads
    the `dev` commit through `git archive`, and a test shows an ignored leftover staying out.
  - The hook's rule on moving `main` caught `main-old` and `update-ref refs/heads/dev main`, and
    missed `fetch . dev:main`, `push . HEAD:main` and `branch main -f`. All six are now tested.
  - Refusals without a test now have one: a file that can't be stamped, a template without its
    markers, `main` checked out in a worktree, and `--preview`.
  - A child Python that failed without a message crashed the refusal. It now says so.
- **Standards:**
  - The two constants' cheat-sheet lines now say what each is, from the sentence of the Toolbox
    docstring that starts with its name.
  - `example_database.py`'s file line repeated its one name's line word for word, so it is left
    out.
  - The file listing written twice is one `files_in`, and `WORK_HAS` no longer lists
    `__future__`, which the standard library already covers.

Answered, not changed:

- **The export checks the import allowlist itself,** though `tests/test_toolbox_checks.py` already
  does on `dev`. The ticket's owner asked for it, and it checks the stamped copy that ships, not
  `dev`'s.
- **ruff now also checks `tools/`,** which no ticket asked for. It holds the export to the same
  complexity limit as the rest, at no cost.
- **The update-ref old-value guard has no test.** Two exports would have to race, and git's own
  compare-and-swap is what's relied on.
- **`refusals.py`'s line names Guards and a Warning, and lists only the two exceptions.** The
  Warning's category isn't a public name (ticket 18), and the line is that file's docstring.
- **"Clean tree", "build" and "hash" in `tools/export_clean.py`.** "Clean tree" is ticket 13's
  word. "Build" and "hash" are on the glossary's _Avoid_ list as names for a Toolbox version, and
  here they mean a git object and the act of building, in a `dev`-only tool.
- **The cheat sheet's `__init__.py` heading** sits under a line that says to import every name
  from `sql_composer` itself. The headings say where each name lives, which is how the ticket
  groups them.
- **Smells left,** since standards.md prefers plain repetition to machinery:
  - `described` travels as a dict, because it crosses a JSON boundary from the child Python;
  - `export` runs one `subprocess.run` by hand for a `main` that may not exist;
  - the hook's three patterns repeat the `git` prefix.

**Beginner reader (2026-09-25).** Report:
[reports/19-beginner-reader.md](../reports/19-beginner-reader.md). Its advice is for the user. It
found two outright bugs, fixed in `f478f40`:

- the Toolbox docstring's `>>> VERSION` showed `'SQL Composer 2.0, not exported (dev)'`, which
  was false in every exported copy. It now shows `'SQL Composer 2.0, ...'`, and a test holds it
  against the exported value;
- the README said every cheat-sheet name has a Worked example, which the two constants don't,
  and a pasted docstring example failed on `jobs`. It now says what to run first.

Its costliest stops, for the user to weigh: what `CROSS_JOIN`'s "its name is the opt-out" opts
out of; how to write your own `send` at work (`help(by_day)` uses an undefined `run_query`); and
that docstring examples using `last_n_days` only reproduce on 2026-09-25, since the Example
database holds two days.

## Answer

**The Clean-branch export is built, and it has replaced `main`'s v1 draft.** Commits 3ea25aa,
6d608d0, 2ed073a, 8682218, 200514b, 70c2ac5, fd622bc and f478f40, then the export itself.

- **`tools/export_clean.py`:** run `python tools/export_clean.py` on a clean `dev`. It builds
  the Clean tree in a temporary folder from the `dev` commit, then:
  - stamps line 1 of every Toolbox file (`# SQL Composer 2.0, exported ... - generated from dev,
    do not edit`, or an HTML comment in Markdown);
  - writes the file list into `__init__.py`'s `_FILES`;
  - writes `.github/README.md` from `docs/clean-branch-readme.md`, with the version and the
    cheat sheet: one line per public name, grouped by file, from each docstring's first line.

  It checks the import allowlist, imports the stamped copy in a fresh Python, and checks that
  the tree holds only `sql_composer/` and `.github/README.md`. Then it commits the tree to `main`
  locally, on top of the old `main`, without checking `main` out. It never pushes. It refuses off
  `dev`, with uncommitted changes, while `.scratch/drift.md` has an open item under `## Items`,
  and while `main` is checked out in a worktree. `--preview <folder>` builds without git.
- **Tests:** `tests/test_export_clean.py` runs the same build without git, and checks the
  allowlist, the stamp, the file list and the README. It also runs the git side in a throwaway
  repo, the refusals, and the README template's examples as doctests. The pointer test reads the
  template. 656 tests pass.
- **The hook** (`.claude/hooks/protect_main.py`) lets only the export run alone through, and
  refuses moving `main` by hand. `tests/test_hooks.py` covers both.
- **Docs:** `CLAUDE.md` says how `main` is exported, and `CONTEXT.md`'s Clean branch holds the
  README too.
- **Drift:** D6 and D7 opened and closed in 2ed073a, and nothing is open.
- **The export** ran once after this ticket resolved. The old `main` was `3c13898` (see above),
  and it stays as the new `main`'s parent. **Pushing `main` is the user's step.**

Beginner reader: .scratch/sql-composer-v2/reports/19-beginner-reader.md
