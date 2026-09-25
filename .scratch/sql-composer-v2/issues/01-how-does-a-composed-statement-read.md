# How does a composed Statement read?

Type: prototype
Status: open
Blocked by: -

## Question

Readability for a Python-first SQL beginner is the top priority, and most other tickets hang off
this one. Make the question concrete. Pick two or three realistic queries of the kind the user
will write - for example: a count of failed rows by week and by one attribute over the last N
days; a two-table join narrowed by a filter that comes from a Building block; the latest row per
key. Write each in two or three candidate styles, across all three Levels (the Table reference it
uses, the Building block it borrows, the Statement itself), and show the Hive string each emits.

Candidate styles to include at minimum: a thin layer over sqlglot's own builder; clause functions
that return pieces, in the user's words "SELfunc(params) FROMfunc(params)"; and whatever else the
prototype suggests. Put them side by side and let the user react and choose.

The choice fixes the vocabulary every later ticket uses: how a column is referenced, how a
Building block plugs into a Statement, and how a Statement becomes a string.
