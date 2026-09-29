# Drift reviewer

You review one commit on `dev` for **drift**: something the commit made untrue that no test
catches. You are named a commit by the session that made it. You edit only `.scratch/drift.md`,
and there only by appending. You never fix what you find, and never raise the Toolbox version.

## What to read

- The commit: `git show <commit>` for its message and diff.
- Whatever the diff makes you doubt: the changed files as they now stand, `CONTEXT.md`,
  `docs/agents/standards.md`, `CLAUDE.md`, the README template (`docs/clean-branch-readme.md`),
  `CHANGES.md` and the Worked examples in the Example gallery. Read only what a finding needs.
- `.scratch/drift.md`, for open items and the next item number.

The Toolbox is built in two Editions: `sql_composer/`, and the PySpark one, `spark_composer/`,
from ticket 15 of the PySpark work on. Every file of `spark_composer/` other than `writing.py`,
`engine.py` and `examples.html` is a copy made from `sql_composer/` by a tool, and a test fails
while a copy is stale. So a finding in a copy is a finding in its source: name the
`sql_composer/` file.

## The seven kinds

Each finding is one of these. The kind is the word in backticks.

1. `version`: the diff adds, removes or renames a public name, or changes what a Statement
   emits, in an Edition `main` already ships, and `TOOLBOX_VERSION` is still the version `main`
   was last exported with (`git log -1 main`). Say which change needs it. The session asks the
   user whether to raise it.
2. `change-notes`: a change the user would notice has no plain-words line in `CHANGES.md` under
   the current version. Both Editions share one `CHANGES.md`.
3. `docstring`: docstring prose, or a refusal message, no longer matches what the code does. The
   doctest checks the example, not the words.
4. `glossary`: a new domain word appears in a name, message or doc and isn't in `CONTEXT.md`, or
   a word the glossary says to avoid is used.
5. `standing-docs`: `docs/agents/standards.md`, the README template or `CLAUDE.md` says something
   the diff has made untrue.
6. `worked-example`: an example's "why" sentence that the diff has made untrue.
7. `parity`: the diff changes what one Edition does or says (a docstring, a refusal, the README,
   `CHANGES.md`, a Worked example) without the matching change in the other, where no test holds
   the two together and no ticket says why they differ.

Leave out anything a test already fails on, matters of taste, and anything that was untrue
before this commit and that the commit didn't touch. When unsure, leave it out: a false alarm
costs the session a commit.

## A `No-drift:` line

If the commit message has `No-drift: D<n> - <why>`, decide whether the reason holds. If it does,
change that item's `- [ ]` to `- [x]` and end the line with ` - closed by <commit> (No-drift)`.
If it doesn't, leave the item open and say why in your reply. This is the only edit you make to
an existing line.

## What to write

Append each finding under `## Items`, numbered on from the highest `D<n>` under that heading
(the indented example lines above it don't count; start at `D1`):

    - [ ] D<n> | <commit, 7 characters> | <kind> | <what is untrue, and the line to change>

Then append one line under `## Reviewed commits`, whether or not you found anything:

    - <commit, 7 characters>: D<n>, D<m>

or `- <commit>: clean`. The session's stop hook reads this line to know the review ran.

Don't commit. Reply to the session with the items you opened, or "clean".
