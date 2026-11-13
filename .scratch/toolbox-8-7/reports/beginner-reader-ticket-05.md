# Beginner reader: ticket 05, bold colours

Run 2026-11-13, `beginner-reader` on Opus, twice: first on headless Chrome screenshots of the
before and after pages in `ticket-05/` (the screenshots kept outside the repo), with a first
palette (shared tables orange, Python step blue with white text,
conditions purple) and a regenerated Example page, then on the final palette. Advisory only.
What came of each stop follows each report.

## The report

**Better than before**

- On the Statement page and the Scheduled run page the kinds are now easy to tell apart at a
  glance: blue table columns, green outputs, pink conditions, orange Unchecked statement. The
  legend swatches finally show something; before they were near-white squares I couldn't
  match to anything.
- The black edges on Unchecked, Python step and shared tables make them stand out on purpose.

**Stops**

1. **The loop page, "is drawn red"** (`project_lineage.py:511`). The banner and the loop
   edges now come out orange (vermillion `#D55E00`), not red. The two loop boxes are ordinary
   sky-blue boxes with a thin orange outline, so they look almost like `mart.team_count`
   beside them. Before, the red banner and red boxes said "error" straight away. Now the
   banner is the same family of colour as the "written by more than one Scheduled run"
   warning, which the page itself says is "shown, never refused". The worse problem now looks
   like the milder one. **Stuck**: I reread the banner to be sure this was really a refusal.
2. **A shared table in a loop** (`html_page.py:99-100`). If a table is both shared and in a
   loop, the loop's vermillion edge replaces the black one on an orange fill. Orange on orange
   will be close to invisible, so that box would read as only "shared" and the loop would
   disappear. **Reread.**
3. **The same colour means different things on different pages.** Pink is "condition" on the
   Statement page but "read, not written here" on the Project page; green is "output column"
   on one and "Saved table with no Table folder" on the other; orange is "Unchecked statement"
   and "written by more than one Scheduled run". Orange works, since both are warnings with
   the warning sign. Pink doesn't: an outside table isn't a condition. **A reread.**
4. **Python step blue next to table-column sky blue.** Without the black edge and white text
   I'd have read it as another table column. **A moment.**
5. **A yellow "Derived table column" swatch with no yellow box.** Now that the swatches are
   bright, a kind the page doesn't have stands out more than before; the same for Unchecked
   and Python step in the Scheduled run page's legend. **A moment.**
6. **The Run value box "logic of mart.team_jobs.first_job... gave 1"** is sky blue like a
   table column, and no legend entry names it. **A moment.**
7. **Text on green boxes**: the small monospace lines are harder to make out on `#009E73`
   than on the old pale green. They may pass 4.5:1, but at 11px they're the tiring part of
   the page. The white text on the Python step blue reads fine. **A moment.**
8. **Nothing looks like an error that isn't one** on the Statement and Scheduled run pages.
   The dashed condition boxes in reddish pink look a little alarming, no worse than
   "noticeable".

**The three costliest stops**

1. The loop is less obvious and no longer looks like an error.
2. A shared table in a loop would hide the loop.
3. Pink and green change meaning between the Statement page and the Project page.

## What came of it

The palette then changed again on the user's words ("just pick a color palette that's
saturated and diverse enough. Shouldn't need to get too creative with font colors"): one dark
text on every fill, the Python step reddish purple, condition and read-only tables grey.

- Stop 2, fixed: shared tables are yellow, so a loop's vermillion edge shows on them, and the
  Project page has no orange but the loop's.
- Stop 1: kept vermillion at first; the second read found the same, and the loop went back
  to red (below).
- Stop 3, fixed: read-only tables are grey and dashed, as conditions are, so no hue means two
  things across the pages but a Table folder's sky blue and a Saved table's green, which keep
  a table column's and an output column's.
- Stop 4, fixed: the Python step is reddish purple, no longer a second blue.
- Stop 7, fixed: a box's lines after its first are black (`box-text`), 6.1:1 on the green.
- Stops 5 and 6, outside this ticket: the legend lists every kind of its page, and a Run
  value's box is drawn as a table column, as before the colours changed.

## The second read, on the final palette

Run the same day on the after screenshots of the palette above (with the loop still
vermillion). Every kind was easy to tell apart and match to its swatch; the cost was the loop.

1. **The loop no longer looks red** (stuck). The 2px vermillion edge on sky blue reads as
   orange, close to Unchecked's; the loop's boxes were found only after reading the banner,
   and the page says a loop is "drawn red" (`project_lineage.py:510-511`, `:723`).
2. **Yellow means two things** (a reread): Derived table column on a Statement page, the ⚠
   shared warning on the Project page; the warning boxes didn't look like warnings until the
   ⚠ was seen. Blue, green and grey reuse harmlessly.
3. **The thick black edge mixes warnings with a non-warning** (a moment): Python step shares
   it with the two ⚠ kinds.
4. **Grey looks switched off** (a moment) for a condition; it fits "read, not written here".
5. **Small text on saturated fills** (a moment): readable, about 6:1 on green, but a page of
   blue, yellow and green is heavy, and the faint dotted arrows are harder to follow on it.

What came of it:

- Stop 1, fixed: the loop is red `#d33` again, as before the ticket, and its note `#a11`; the
  red is the loops' alone, since the lit path is black.
- Stop 2, kept: yellow is the one Okabe–Ito hue left on the Project page that a loop's red
  edge shows on; the ⚠ in the box and the legend say it's a warning.
- Stop 3, kept: the black edge marks a box to look at, as the coloured edges did before; only
  the colour of the edge changed in this ticket.
- Stops 4 and 5, kept for the user's testing ("subject to testing"): the dashed grey was the
  condition's look before, a shade darker now; a lighter palette is an edit to the tokens.
