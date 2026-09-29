# How does the Toolbox survive being pasted over an existing directory?

Type: grilling
Status: resolved
Blocked by: -

## Question

At work the user pastes files on top of an existing directory, overwriting on a name clash. Their
own scripts sit beside the Toolbox and import it laterally. Pasting never deletes anything, so a
Toolbox file that is renamed or removed in a later version stays behind, still importable, quietly
serving old code.

Decide:

- the Toolbox's shape - one file, a few flat files, or a package directory;
- names that cannot collide with the user's own files;
- what happens to a removed or renamed file - a frozen file list, an import-time check for stray
  files, or an explicit "delete these" note with each drop;
- how the user tells which Toolbox version is installed.

Keep the copy cheap: every file is a manual paste.

## Answer

**A package folder, `sql_composer/`, which checks itself on import and stops if the paste left it
inconsistent.** At work the user downloads the Clean branch as a zip, extracts it and copies the
files over the existing directory; the worst case is pasting text file by file. The install is
fresh, with no v1 leftovers. The user chose a package folder over a single file, so stale files are
managed by a check rather than ruled out by the shape.

- **Shape:** `sql_composer/`, flat inside, with a few modules and no subfolders. How the modules
  divide the Toolbox is decided in "What's in the Toolbox?". The user's scripts import only from the
  top level (`from sql_composer import ...`), never from a module, so moving a function between
  modules never breaks them.
- **Names:** the `sql_composer` prefix belongs to the Toolbox, and the user's scripts never use
  it. The Clean branch's README lives at `.github/README.md`, so GitHub still shows it on the front
  page but it can't overwrite a `README.md` of the user's. The zip root then holds only the
  `sql_composer/` folder, so "copy everything" is safe.
- **Updating:** the documented steps are *delete the `sql_composer` folder, copy in the new one,
  restart the kernel*. The user's scripts sit beside the folder, never inside it, so deleting it
  is always safe. The restart is needed because a running kernel keeps the old code in memory.
- **Self-check on import, which stops with a plain message rather than warning:**
  - **Extra files**, such as a module dropped in a later version or a script put inside by mistake.
    `__pycache__` is ignored.
  - **Missing files**, such as one forgotten during a text paste.
  - **A `TOOLBOX_VERSION` that differs between files:** *"sql_composer 3.1: `lineage.py` is from
    2.7 - paste it again from the 3.1 download."*
  - **An export stamp that differs between files,** which catches a leftover from an earlier drop
    of the same feature number.

  The file list is written into `__init__.py` by the export script, where it can be read.
- **Versions:**
  - `TOOLBOX_VERSION = "3.1"` sits at the top of every file as code on `dev`. It is a feature
    number, raised by hand only for a big feature, and a `dev` test fails if any file disagrees.
    The user asked for this so that end-to-end consistency is tested explicitly on `dev`.
  - The export script adds line 1 of every file:
    `# SQL Composer 3.1, exported 2026-10-02 14:05 - generated from dev, do not edit`. The export
    time never causes edits on `dev`.
  - `sql_composer.VERSION` gives the same text, and every lineage HTML and Markdown export shows
    it, so an old report or a stale kernel shows which Toolbox made it.
  - `sql_composer/CHANGES.md` keeps the full history in plain words, grouped by feature number. It
    lives inside the folder, so it is copied with it.

Ruled out:

- **A single `sql_composer.py`,** which would have removed stale files by shape.
- **Merging updates into the old folder** as the documented route.
- **Warning instead of stopping,** since a warning is easy to scroll past.
- **Per-module API versions with compatibility ranges,** since every file in a pasted folder should
  come from the same drop.
- **Printing the version on every import.**
- **Stamping the version into the SQL string,** since it's unknown how the query API treats a
  leading comment.
- **`%autoreload`,** which is left to the run-loop fog.

## Comments

**The user's decision (2026-09-25): "make all import stops four-part".** Every stop of the
import self-check now has the four parts a refusal has (what happened, why it matters, the
usual fix, and "Opt-out: none", since no import stop can be switched off), built by the one
four-part function. Each still raises `ImportError`. This replaces the one-line shape decided
above, such as *"sql_composer 3.1: `lineage.py` is from 2.7 - paste it again from the 3.1
download."*: that stop now says `lineage.py is from Toolbox version 2.7, and __init__.py is from
3.1.`, and its fix is to delete the folder and copy the whole folder in again from one download,
which is right whichever of the two files is the stale one. An extra file's fix now says to move
it out first if it is one of the user's own scripts, so deleting the folder doesn't lose it.
Tests first, one per stop, in `tests/test_import_self_check.py` (ac2d38a). The work is recorded
in "Build the Toolbox core" (ticket 18).

**Changed by the PySpark edition (2026-09-29).** The zip root will hold two folders from 3.0,
`sql_composer/` and `spark_composer/`, one per Edition; the user copies the one work uses,
whole. Each folder checks itself on import exactly as decided here, and a file pasted in from
the other Edition stops the import too.
