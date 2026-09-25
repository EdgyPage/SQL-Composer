# What does the work environment actually have?

Type: task
Status: open
Blocked by: -

## Question

The build targets the work environment, and these facts can only be read there. This is a
checklist for the user to run at work; record each result in the Answer.

- **Python version** - `python --version`.
- **Library versions** - `sqlglot.__version__`, `pandas.__version__`, `numpy.__version__`.
  sqlglot matters most: v1 targets 30.18.0, older releases lack APIs it used, and sqlglot's minor
  releases break APIs by policy.
- **Notebook environment** - Jupyter, JupyterLab, Databricks, VS Code, or something else.
- **The query API** - what does one call return (a DataFrame, a list of rows, a job id to poll)?
  Is there a row limit or a timeout? Does one call accept more than one statement? Can results be
  fetched in pages?
- **Network** - can the machine that opens an HTML file load anything from the internet, or is it
  offline?
- **The Hive cluster** - its Hive version (`SELECT version()` if the API allows it, or ask the
  platform team), whether any `hive.strict.checks.*` are switched on, and whether the API accepts
  a `SET ...;` statement ahead of a query. The Hive research found strict mode unreliable, so the
  Toolbox enforces its own defaults either way; these facts decide whether they duplicate the
  cluster's checks or stand alone.
- **Files** - can a notebook write a file (the lineage HTML) somewhere the user can then open in a
  browser?
- **Inline scripts** - does the work browser run JavaScript in a local HTML file? Open
  `research/offline-graph-html/lineage_prototype.html` (from the `research/offline-graph-html`
  branch) from disk and see whether clicking a node highlights its path. If scripts are blocked,
  the lineage view falls back to a script-free tree.

The sqlglot version gates "Which sqlglot APIs can the Toolbox use at work?"; the API's behaviour
gates the load-safety and Table-reference tickets.
