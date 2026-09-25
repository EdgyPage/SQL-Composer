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
- **Files** - can a notebook write a file (the lineage HTML) somewhere the user can then open in a
  browser?

The sqlglot version gates "Which sqlglot APIs can the Toolbox use at work?"; the API's behaviour
gates the load-safety and Table-reference tickets.
