# The repo's own guards

Type: task
Status: claimed
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
