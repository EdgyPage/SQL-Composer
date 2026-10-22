# tools/: shared pieces of the page generators

Type: task
Status: resolved
Blocked by: 17
Size: S

## Question

The plan's optional ticket 18: low usage. `prose_html` shared by how_to_page and
example_gallery; code_audit and offline_policy stay independent readers unless a shared piece
is trivially small.

## Done when

- Done or answered in the ranking: what was merged, what was left and why.

## Answer

- **Merged:** `prose_html`. how_to_page's copy, which keeps indented code with blank lines in it
  as one block, moves to example_gallery with its `paragraphs` and `is_code`, and takes how a
  line of words is shown: the gallery's `inline` by default, the how-to page's `linked`. The
  gallery's own copy goes. Both pages regenerate byte for byte the same, so no docstring the
  gallery shows had two code blocks in a row. Net, tools/ is 17 lines shorter.
- **Left:** code_audit and offline_policy. What they share is a notebook's cells read from its
  JSON and a cell's source joined, about three lines, and the two handle a notebook they can't
  read differently on purpose: the offline policy reports it, the audit leaves it to the policy.
  code_audit already walks the repo with the policy's `not_read`, so the folders each skips
  can't drift apart. They stay two readers, as the plan says of security readers.

## Reviews

Code review of 4477331 (review-standards and review-spec, Sonnet):

- Standards: no hard violations. Fixed: the script-docstring helper's local `paragraphs`
  shadowed the new function (now `parts`), and `is_code` had no docstring. Left: renaming
  `prose_html`'s `line=`, which reads plainly as "how a line of words is shown".
- Spec: nothing missing, no scope creep. The one possible difference: two code blocks in a row
  in a docstring the gallery shows would now be one block, as the how-to page has always shown
  them. None does today (both pages regenerate the same), and one block is the better showing
  of code with a blank line in it, so no test pins the old split. The Answer's line count is
  reworded.
