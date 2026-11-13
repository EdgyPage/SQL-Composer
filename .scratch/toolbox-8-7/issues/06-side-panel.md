# The side panel and minimal Markdown

Type: task
Status: open
Blocked by: 04
Size: L

## Question

A long step's text runs past its box, and its full Hive sits in a report below the drawing
(Q3, Q4, Q14). What does a click show, and what does Markdown keep?

## Done when

- **The panel.** On all three lineage pages, the Scheduled run's included, clicking a box opens
  a panel beside the drawing, and still lights up its path. The panel shows:
  1. the step's full Hive, wrapped, with a Copy button;
  2. the tables it reads and the tables it writes;
  3. its Run values, and the Session settings sent before it;
  4. on the Project page, the Scheduled runs that write the table.
- A click off every box closes the panel. Escape closes it too.
- It works with the keyboard: Tab reaches each box, and Enter opens its panel.
- The report below the drawing goes.
- **The Markdown page** keeps each table or step, what it reads and writes, and its Hive in
  full. The drawing, the panel, the path lighting, zoom and the colours are HTML only.
- A test holds that each line of a page's Markdown, its Hive included, is in its HTML too, for
  all three exports.
- The panel's script is in the page module (ticket 04), and the pages pass the offline policy.
- The README's lineage paragraphs and the how-tos that show lineage say what a click shows.
