# Beginner reader: Toolbox 8.6's new surface (ticket 10, 2026-11-09)

The `beginner-reader` agent (model `opus`), over what a beginner sees that 8.6 changed:
connect's refusal and warehouse.py, the scheduled_run Template and weekly_team, the
parameters' refusals, the docstrings of build_run, new_scheduled_run, remove_scheduled_run,
describe_logic, export_run_hive, export_run_lineage, export_project_lineage and BuiltRun.run,
the README's new sections, how-to 31 and Copilot files 18 and 00. Its report, as given (line
numbers are of the files before ticket 10's mends); what was done with each stop is in ticket
10's Answer.

## Stops

**connect and warehouse.py (`sqlglot_composer/project.py`)**

1. **Line 220**, in WAREHOUSE_TEXT: "You pick which one sends each Statement, by calling
   run_query(s, query)...". In a Scheduled run, `built.run(query, execute)` picks for me, so
   this rule seems not to hold there. A moment.
2. **Line 253**, connect's refusal: "change the functions in your Project's warehouse.py". The
   README (line 158) says of warehouse.py "you fill in nothing". So may I edit it or not? A
   reread.

**Scheduled run Template (`example_projects/intermediate/admin/templates/scheduled_run.py`)**

3. **Lines 10-11**: "`<LOGIC_FUNCTION>` ... such as `week_totals(WEEK)`". The real
   `week_totals` takes `(first_day: str, last_day: str)`. The README writes
   `week_totals(first_day, last_day)`. weekly_team passes `run_value(week_first_day),
   run_value(week_last_day)`. Three spellings for one call, and the Template's has the wrong
   number of arguments. The same `week_totals(WEEK)` is in the `_refuse_given` fix
   (`scheduled_runs.py` line 686) and in the describe_logic docstring (line 7692). Stuck.
4. **Line 30**: "**Connect.** Goal: this run's account." What account? Worked out later, from
   the README's "the account this run runs as". A moment.
5. **Line 47**: "The writes of each table of this Project the Statements read are added, all
   the way up". I asked for one SELECT, and it will rewrite the tables above it? A reread.
6. **Line 92**: "through run_value(...), is a Run value too". `run_value` isn't imported in
   the Template's cells. A moment.
7. **Line 110**, the Run cell comment: `results["<RESULT_NAME>"]`. In the filled-in
   `weekly_team.ipynb` (cell 5) this placeholder is still there, and the Build cell comment
   there names `RUN_DATE`, which that notebook doesn't have. The Self-check says "No code
   cell holds a `<...>`", so I wondered if the example was unfinished. A reread.

**weekly_team (`scheduled_runs/weekly_team/weekly_team.hql`)**

8. **Lines 30/66/103 vs 118**: the added writes cover '2026-09-22'...'2026-09-24', but the
   SELECT reads '2026-09-21'...'2026-09-27'. WEEK steers only the SELECT. Passing
   `-p WEEK 2026-11-04` would rewrite September and read November. Nothing says the
   parameters don't reach the writes the build adds. Stuck.

**Parameters' refusals (`sqlglot_composer/scheduled_runs.py`)**

9. **Lines 147-151**: "Tag the cell parameters: in Jupyter, View, then Cell Toolbar, then
   Tags". That menu exists only in classic Notebook; JupyterLab and VS Code do it another
   way. It is also the first time I'm told papermill is a tool. A reread.
10. **Lines 99-104**: "the parameter {name} isn't set in this notebook ... Run the notebook's
    cells from the top". Clear, but it showed that build_run reads the names from the saved
    file and the values from my live Python. A moment.

**Docstrings**

11. **build_run, lines 7338-7344**: the example uses `statement`, `SELECT`, `job_runs` and
    `equals`, none of them imported. A moment.
12. **build_run, lines 7372-7373**, repeated in the README and Copilot 18: "in place of what
    its function gives, a write() that takes nothing among them". I couldn't parse it. Stuck.
13. **build_run, line 7380**: "leave_out=[...] leaves one out, with what only it reads". A
    reread.
14. **build_run step 5, lines 7388-7399**: Guards only warn in the `# scheduled` cell. A long
    list of which Guards relax and which don't, and no reason why a scheduled job should be
    laxer than a notebook. The README and how-to repeat it. A reread, twice.
15. **export_project_lineage, lines 7449-7450**: the only example output is a failure: "cell
    4 of ... isn't Python yet, at its line 12". I had to count cells, the markdown cell
    included. A moment.
16. **remove_scheduled_run, line 7337**: `# the time it ran, as yyyymmdd-hhmmss` sits on the
    call line, but explains the `...` in the output below. A moment.
17. **describe_logic, line 7690**: "paste what it gives under Copilot file 18". Under means
    after the file's text, in the same chat? A moment.

**README (`docs/clean-branch-readme.md`)**

18. **Lines 104-107**: `connect(my_api.connect())` with no `from warehouse import connect`
    before it. Line 98's "in its first code cells" (plural) left me asking which cell. A
    moment.
19. **Line 1365**: "A cell of your own beside it, such as a user ID, is yours: it isn't
    read." A cell such as a user ID? A reread.
20. **Line 1391**: "Arguments to a logic function, as in step 5, are the other way in." With
    `run_value(...)` and `run_values=`, three ways to feed a value and no table saying which
    to use when. A reread.
21. **Lines 1708-1709**, the 8.5 bullet: "keeping your `conn = ...` line ... marked to move
    into a `connect(...)` call". Move it where, warehouse.py or each notebook? A reread. Also
    `version.txt` and Copilot file 18's title say "8.5", while this README talks of an 8.6
    Upgrade. A moment.

**How-to 31 (`worked_examples/how_to/31_schedule_a_run.py`)**

22. **Lines 62 and 121**: write()'s docstring says "the last 3 days, ending on DAY", and the
    run also defines its own `DAY`. I assumed the run's DAY (2026-09-23) feeds write(). The
    output still writes '2026-09-22'...'2026-09-24'. The same trap as stop 8, made worse by
    the shared name. Stuck.

Smaller how-to stops:

- **Line 68**: the example SELECT, `team_day_from_job_events`, reads only ops tables, so the
  run's result doesn't depend on what it just wrote. A reread.
- **Line 144**: the key `"team_days"` for a write is never shown; the heading says
  `mart.team_days`. What is the key for? A moment.
- **Lines 216-218 vs 322 and 327**: the build prints the SET lines before each of the three
  writes, but the run sends them once, first. A reread.
- **Line 145**: why `str(DAY)` for a date parameter? Copilot 18 answers it, the how-to
  doesn't. A moment.

**Copilot files 18 and 00**: no new stops beyond the "8.5" title (stop 21) and the shared
items 12 and 20.

## The three costliest stops

1. **The parameters don't reach the writes the build adds** (stops 8 and 22). A scheduler's
   value changes only the SELECT; the upstream tables are rewritten for whatever days their
   own Run values give. Nothing says so, and the shared name `DAY` invites the wrong guess.
2. **Feeding a value into the Statements** (stops 3, 12 and 20). The Template's
   `week_totals(WEEK)` disagrees with the real signature and with both examples. Arguments,
   `run_value(fn)` and `run_values={"name": ...}` are three channels with no rule for which
   to use, and "a write() that takes nothing among them" didn't parse.
3. **Guards only warn in the `# scheduled` cell** (stop 14). A long list of which Guards relax
   and which still refuse, with no reason a scheduled job should be the place to loosen them.
