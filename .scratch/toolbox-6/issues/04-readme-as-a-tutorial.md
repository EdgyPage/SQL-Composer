# README as a tutorial

Type: task
Status: open
Blocked by: 03
Size: M

## Question

Map Notes, "The README and the history". Move "Update from 4.x", "Update from 3.x" and each
section that says what a version added out of `docs/clean-branch-readme.md` into CHANGES.md.
Reshape the README into a tutorial skeleton whose steps each link a how-to (the steps that need
Projects are filled in by ticket 10). Add the test that holds the shape and the drift reviewer's
standing-docs line.

## Done when

- The README has no version headings or "Update from" sections, a test says so, and every
  how-to it names exists.
- The pytest runs pass, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).
