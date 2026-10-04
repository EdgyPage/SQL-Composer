# The repo's own guards

Type: task
Status: resolved
Blocked by: -

## Question

The hooks that keep `main` clean and the drift log honest have holes in exactly the glue no
test drives (candidate 10 of [report.html](../report.html)):

1. **protect_main lets main move by hand**: `git checkout -B main`, `git switch -C main`,
   `git branch -D main` and `git branch -m main ...` go through, and so does a commit chained
   after `git checkout -q main`, since a flag between `checkout` and `main` hides the switch.
2. **The drift review sees only HEAD**: a merge commit's `diff-tree` lists no files, so merged
   work is never reviewed, and a rebase or `cherry-pick A..B` that writes several watched
   commits gets one request, for the last.
3. **Any git command that mentions a commit word counts as one**: `git log --grep=revert`
   makes the review hook look for a commit to review.
4. **The gallery tool lists a Worked example's Statements outside `example_setting()`**, so a
   Statement that warns would fail the tests under `-W error` though the tool itself works.
5. **Untested**: the hooks' `main()` glue.

## Decisions (made under the user's goal to implement every candidate worth it, 2026-10-03)

- **protect_main** refuses a forced checkout or switch to main, deleting or renaming main, and
  a switch to main with flags before its name.
- **The review hook asks for every new commit**: each commit on dev that its upstream hasn't
  got, oldest first, that touches a watched path and was neither asked for nor reviewed. A
  merge's files are its changes against its first parent. Without an upstream, HEAD alone.
- **A commit is a git command whose subcommand makes one**, after git's own options:
  commit, merge, pull, cherry-pick, revert, am or rebase.
- **`other_statements` runs inside `example_setting()`.**
- **Tests drive the hooks' `main()`** against a throwaway git repo.
- **Not done, as not worth it:**
  - removing EXPORTED and the one-Edition export branches, which a test exercises and a
    future Edition could use;
  - one parser for an open drift item, since the stop hook needs the commit field the
    export doesn't, and the two agree on every item the reviewer writes;
  - one list of the Toolbox's modules, since the test's own glob is an independent check.

## Done when

- Each of 1-5 has a test.
- Both runs pass.
- The code-review skill has run with this ticket as its spec.

## Answer

Built in `20adef4`, reworked after the review in the commit after it (see the log).

- protect_main refuses a forced checkout or switch to main, deleting or renaming it, and a
  switch to main with flags first; a branch named like main-fix isn't taken for main.
- The review hook asks about each new commit on dev since its upstream (none when there is
  nothing new), a merge by its first parent, finding the drift list from the repo's top
  folder wherever it runs. The stop hook forgets a commit a reset or a rebase dropped.
- MAKES_A_COMMIT takes git's own options quoted or not, and only a subcommand that makes a
  commit: not merge-base or commit-tree, nor the git in `.git`.
- The gallery tool lists a Worked example's Statements inside example_setting().
- tests/repo/test_hooks.py runs each hook's main() as Claude Code does, against a throwaway
  clone; tests/test_example_gallery.py holds the example day.

**Code review (2026-10-03), `20adef4`.** No hard violations. Fixed: the switch-to-main pattern
matching main-fix; the drift list found from the raw cwd; HEAD asked about when there was
nothing new; hyphenated subcommands, quoted options and `.git` in the commit pattern; stale
requests in the stop hook; the untested gallery fix and hook main()s. Left: a command whose
text quotes a git command, as in a heredoc, is still read as running it, since telling them
apart needs a shell parser; and `git checkout -- main` or `git switch --detach main` before a
commit are refused, which errs on the safe side.
