# README as a tutorial

Type: task
Status: resolved
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

## Answer

Built on the branch `toolbox-6/04-readme-tutorial`.

- `docs/clean-branch-readme.md` is a tutorial: eight numbered steps (install, start a notebook, a
  first Statement, your own tables, filter count and join, save a table every day, Lineage, lay
  out a project), most linking the how-tos that walk through them on
  `../sqlglot_composer/how_to.html#<slug>` (the README is `.github/README.md` on main, so its
  links go up one folder). Then the how-tos, listed by the export as links, the Example gallery,
  Example projects, Templates, the Spark notes, a short Update, the license and the cheat sheet.
- Gone from it: "Update from 4.x" and "Update from 3.x", which CHANGES.md already holds under
  5.0's and 4.0's "To update", and the feature sections written for 5.0 (Keys and storage,
  Session settings and the admin module, joins and windows, keeping reads fast), which the
  how-tos cover and the how-to list now links. CHANGES.md's 6.0 notes say so.
- `tests/repo/test_readme_shape.py` holds it: no heading about one version, numbered steps first
  and in order, each step after Install pointing to a how-to or a section, every linked how-to
  real, and a pointer to CHANGES.md. The drift reviewer's standing-docs kind says the same.

### Reviews

- Beginner reader (2026-10-20): the links resolved inside `.github/` (fixed with `../`); Update
  read `VERSION` after deleting the folder and pointed into CHANGES.md the wrong way round (now
  five steps, with a 4.x example and a line for Spark Composer users); CHANGES.md's 5.0 section
  said the README's Update covers two folders (now "said then"); the how-to list wasn't links
  (the export now writes links); Date partition, Key, Guard and the Levels are glossed in place.
- Spec (2026-10-20): nothing lost from the Update sections (CHANGES.md already held them); two
  cautions from the removed 5.0 sections were nowhere else, now in the README: no UPDATE, DELETE,
  MERGE or TRUNCATE on a Saved table (step 6), and Spark refusing `admin.drop_days` (the Spark
  notes). Kept, for the user to confirm: "If your send runs the Hive on Spark", which is about a
  user's own send, not the dropped Spark Composer. Step 8 is ticket 10's to replace.
- Standards (2026-10-20): "tutorial" is the How-to's avoid-word, so CONTEXT.md gains README,
  "a tutorial of numbered steps ... A How-to is never called a tutorial"; CHANGES.md's "said
  then, then" reworded; a long line rewrapped. The link shape written in three places is held
  by a test, and left.
