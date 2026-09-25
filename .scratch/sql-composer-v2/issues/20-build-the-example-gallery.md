# Build the Example gallery

Type: task
Status: open
Blocked by: 15, 18, 21

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
engine and where the scripts sit. The Example database itself is built in "Build the Toolbox
core", and its demonstrations in "Build the Example database's demonstrations".

Done when the `dev` checks pass and the gallery holds every docstring example plus the first
standalone Worked examples, among them the latest-per-key and top-N-per-group patterns that
`row_number`'s docstring points to.

## Comments

**From "What does the Example database demonstrate, and where does it run?" (2026-09-25).**

- **The standalone Worked examples** are the seven demonstrations from "Build the Example
  database's demonstrations", in `worked_examples/statements/`.
- **A demonstration's entry** puts its `careless()` and `fixed()` Statements side by side. Each
  side shows its Hive and its result, with the Guard's refusal or the Warning's message under the
  careless one. The prototype's `demo.html`, tab A, on `prototype/example-database`, is the rough
  shape.
- **The `row_number` and `week_start` entries** show a pandas result labelled "computed in pandas,
  not by running this Hive".
- **On the sqlglot 25.24.2 CI run,** the regenerate-and-compare test skips with a reason.
