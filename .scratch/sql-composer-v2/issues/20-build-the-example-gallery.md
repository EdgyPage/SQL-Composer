# Build the Example gallery

Type: task
Status: open
Blocked by: 15, 18

## Question

Build the generator for `sql_composer/examples.html` and its first standalone Worked examples, as
decided in "What does `dev` enforce, and which maintainer agents does it carry?".

- **Sources:** every docstring's `>>>` example, plus one short Statement script per standalone
  Worked example in the Example database's `statements/` folder. Each script's module docstring
  gives a title and one sentence on why you'd write it.
- **Each entry shows:**
  - its title and why;
  - the Python;
  - the Hive it emits;
  - the result table on the Example database, where the executor can run it;
  - the Toolbox names it uses, worked out from the code.
- **The page:** one self-contained HTML file with no dependency. A few lines of script filter
  entries by any word, but everything is plain HTML, so Ctrl+F still works without scripts. It
  follows the lineage research's approach ("How can one offline HTML file render an explorable
  graph?").
- **Kept in step:** the page is committed on `dev`, and a test fails if regenerating it changes
  it. It sits inside `sql_composer/`, so it ships and is on the self-check's file list.

"What does the Example database demonstrate, and where does it run?" decides the tables, the
engine and where the scripts sit. Building the Example database itself is still in the map's Not
yet specified, and it must exist before the result tables can be shown.

Done when the `dev` checks pass and the gallery holds every docstring example plus the first
standalone Worked examples, among them the latest-per-key and top-N-per-group patterns that
`row_number`'s docstring points to.
