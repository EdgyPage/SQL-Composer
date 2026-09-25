# What does the work environment actually have?

Type: task
Status: claimed
Blocked by: -
Probe: branch `task/work-environment-probe` (commit `611f381`), `tasks/work-environment/work_environment_probe.py`

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

## Comments

**Probe handed over (2026-09-25).** Most of the checklist is now one notebook file, linked on the
`Probe:` line. Paste it into a work notebook as two cells. Cell 1 reads only the notebook's
environment: versions, notebook markers, the sqlglot calls the Toolbox leans on, whether the
kernel can reach the internet. It also writes `env_check.html` and `lineage_prototype.html` into a
`sql_composer_env_check/` folder. Cell 2 needs `run` set to the query function, then sends seven
tiny queries and twelve `SET <property>` reads. None of them reads a table. Each cell prints a
report to copy back.

What the probe can't read, to answer by hand:

- Which notebook product this is, and whether the browser runs on the same machine as the kernel.
- What the two HTML pages show in the work browser, and whether clicking a node in
  `lineage_prototype.html` highlights its path.
- The query API's documented timeout, row limit and paging, if any. The probe only sees what one
  call returns.

**Answered by hand (2026-09-25).**

- **Notebook:** JupyterLab 4.
- **Where it runs:** a managed workspace. The kernel runs on a Linux VM the user has no direct
  access to, so files the notebook writes land on the VM. The HTML test is therefore opened through
  JupyterLab (its HTML viewer sandboxes scripts until "Trust HTML" is clicked), and a Cell 3 was
  added to the probe that renders the lineage prototype inline in the notebook output.
- **Query API limits:** undocumented as far as the user knows; they believe a timeout and row
  limit exist and are generous within reason. Cell 2's 200,000-row probe gives a floor.

Still to come: the Cell 1, 2 and 3 reports and the HTML test results.
