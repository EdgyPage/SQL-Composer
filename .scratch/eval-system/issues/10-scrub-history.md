# Scrub the git history

Type: task
Status: open
Blocked by: 02
Size: M

## Question

The user (2026-11-14): "add to the tickets a scrubbing of the git history to take out my file
paths and other pii from the git history." Ticket 02 stops new records and paths entering git;
past commits on GitHub still hold them.

## Done when

- **A plan, written before anything is rewritten,** in this ticket's Answer:
  - what is removed: the run and memo records ticket 02 untracked (every path under them, all of
    history), and, in every other file and commit message, each absolute local path, the user's
    folder name and email, replaced with `<user folder>` or a relative path;
  - which refs: dev, main, the tag `last-spark-composer`, and every other branch on GitHub
    (`claude/*`, `dev-6863fb`), each named, with which to rewrite and which to delete;
  - the tool: `git filter-repo` (not installed: installing it is a pip install the user approves,
    into dev's venv), with its exact commands;
  - what changes for the user: every commit hash, so CI history, the export's "from dev commit"
    stamps on main and links to commits change; every other clone must be re-cloned.
- **The rewrite runs on a fresh mirror clone,** never this checkout first, with a full backup
  bundle of the original kept locally (`git bundle create`).
- **Checked on the mirror:** the path test from ticket 02 passes over every commit of every ref;
  the suite passes at the rewritten dev tip; main's tree is unchanged but for scrubbed text.
- **The force-push is the user's step:** the ticket ends with the exact commands for the user to
  run, and how to point this checkout at the rewritten history. Nothing is pushed by an agent.
