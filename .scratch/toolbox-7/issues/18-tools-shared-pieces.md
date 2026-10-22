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
  gallery shows had two code blocks in a row. tools/: 29 lines in, 46 out.
- **Left:** code_audit and offline_policy. What they share is a notebook's cells read from its
  JSON and a cell's source joined, about three lines, and the two handle a notebook they can't
  read differently on purpose: the offline policy reports it, the audit leaves it to the policy.
  code_audit already walks the repo with the policy's `not_read`, so the folders each skips
  can't drift apart. They stay two readers, as the plan says of security readers.
