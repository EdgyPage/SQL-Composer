# The docs and the Copilot files

Type: task
Status: resolved
Blocked by: 02, 03, 04, 05, 06, 07, 08, 09, 10, 11
Size: M

## Question

Say what 8.4 changed where a user reads it.

## Done when

- `docs/workflows.md`, the README and the how-tos on converting, Decisions and seeding show a
  Run value answering a tag, `all_tables`, and a seed limit; the how-to on upgrading says any
  version since 8.3 upgrades straight to the newest.
- The Copilot files that teach the convert and promote Workflows and Unchecked text (07, 10,
  13, 16) say it, each at 8,000 characters or fewer, split into a new file if one runs over.
- CHANGES.md's `## 8.4` lists each change.
- The user decides whether the usability loop gains a scenario with Run values and a seed
  limit (map, "Not yet specified").
- The beginner reader reads what changed, its report linked here.

## Answer
Built 2026-11-05.

- **How-to 09** walks the 8.4 way, its steps now 15: step 6's decisions cell answers
  `all_tables` (`location_root`), each table's key and types, RUN_DAY with text, and
  fail_history's `seed` from 2026-09-01; step 7 writes them with `tables=`; step 8 writes
  `building_blocks/run_values.py`'s `run_day()` (`latest_partition(run_alerts.dt, query)`) and
  answers RUN_DAY with it under `all_tables`, the change said "in place of"; step 9 registers
  the file in check_project.ipynb's register cell; step 10 shows the day in the Hive with the
  Table notebook's "Try it" cell; step 12's seed line shows `WHERE dt >= '2026-09-01'`.
- **Its edge cases, written in full after step 15**, as the user asked: what a Run value may
  give, when it runs (each table on its own), where it lives, today and latest_partition on
  non-date Partitions, a tag inside quotes (`tag_text`), `run_value` in a Statement of your
  own; a Run value that runs a query of its own (`last_good_day`, run on the Example
  database); a failed one (`<no_day() failed>`, run_query refusing); `all_tables` with a
  table's own answer over it; seed limits on any partition column, a single value meaning
  "or later". Common mistakes add the nightly tag answered by a Run value, the function written
  with brackets, and a table converted before 8.4.
- **How-to 28** says a Project 8.3 or later last wrote upgrades straight to the newest, and
  points to upgrade.ipynb's step 1 cell; **how-to 29** (written by `tools/workflow_graph.py`)
  says what an answer may be, a Run value's function, `all_tables` and the seed.
- **The README template**: section 9's step 4 is if/then rules (a bare or quoted tag, a Run
  value, registering its file, `all_tables`, a seed limit, answering again); Update's step 5
  points to upgrade.ipynb's step 1 cell and says versions may be skipped.
- **docs/workflows.md** is drawn from workflows.py, whose steps ticket 08 already gave
  `tables=`: the tool writes it unchanged. The teaching is in the how-tos.
- **CHANGES.md's 8.4**: an opening paragraph, "To update from 8.3" (the Upgrade, the Workflow
  notebooks written again, a table converted before 8.4 keeping its seed and its
  `TAGS["NAME"]`, last_n_days in UTC with an example), the "Being built" line gone. Ticket 13
  finishes it.
- **Copilot file 17**, `17_run_values_and_seed_limits.txt`, new, as files 07, 10 and 13 had no
  room: a Run value's function, the decisions cell with it, `all_tables`, seed limits, and the
  edge cases. Like 13, 14 and 16 it leaves out the Always block (its Statement inside a
  function is file 03's): `tests/test_copilot_files.py` lists it so. File 00 routes to it;
  07 (`tag_text` for a quoted tag), 10 (`${hivevar:...}` is Hive), 13 (a Run value in place of
  `${hivevar:...}`) and 16 (a prod copy's TAGS and seed) send users there. Sizes, as
  count_characters counts on Windows: 00 6,795; 07 7,986; 10 7,967; 13 7,989; 16 7,026;
  17 7,688; the rest unchanged.
- **The evaluation**: objective 17, with T47 (dev, a Run value and location_root), T48 (dev, a
  seed limit on a table that reads itself, through the seed) and T49 (held out, every step
  through the compare with a Run value); each reference passes. Not run against Copilot.
- **The beginner reader**, [its report](../reports/12-beginner-reader.md). Fixed: the two step
  numberings (the notebook's step N, everywhere), registering as a step of its own, "that value
  or later" in bold wherever a seed limit is taught, Run value as the value a function gives
  (how-to 09, README, CHANGES), the PARTITION typed in (step 8 says the write still goes to
  that day, and why), the reason prod's seed is its own, the CHANGES example for last_n_days,
  the grammar of how-to 28 and the stops in how-to 09, 29, the README and Copilot 10, 16 and 17;
  docstrings of run_value (split), tag_text (an if/then for `quoted=`), latest_partition (its
  example hinted), hive_date and today.
- **Answered, left as is:**
  - write_decisions' docstring is a wall (stop 7): its restructuring is Toolbox work beyond a
    wording fix, left for the user to call.
  - A single seed value meaning "or later" (stop 6) is the grilling's (Q5, Q22): the docs say
    it in bold; changing it is the user's call.
  - The reference sections sit under `## Steps` as `###` headings (stop 20): a how-to's six
    `##` headings are fixed by its tests, which allow headings not numbered after the steps.
  - The version, 8.3 in file 17's header and how-to 28's output (the reader's note): ticket 13.
- **Found, for the user or a later ticket:**
  - A Script tag in a PARTITION, `PARTITION (dt=<PARM="RUN_DAY"/>)`, is skipped by
    project.convert ("its PARTITION gives dt the value ..., not a plain one"): a nightly script
    whose Partition is tagged can't be converted. How-to 09 says so.
  - A failed run_value of a function made in a notebook names it `None.no_day()` in the
    refusal (its module is None in a doctest; `__main__` in a notebook).
  - script_tag's docstring says a failed tag leaves `<period_end() failed>`; the Toolbox writes
    `<PERIOD_END failed>`, the tag's name, as CHANGES.md now says.
- **For ticket 14, calls no shipped cell makes**:
  - `project.upgrade()` in admin/check_project.ipynb, for a Project made before 8.0, which has
    no upgrade notebook: how-to 28 and the README say to run it there. The Toolbox's own text
    still says "in a new cell" (`refusals.warn_upgrade_needed`, and project.check()'s upgrade
    line).
  - Registering a hand-written Run value's file uses check_project.ipynb's commented
    `project.register(...)` cell, the user writing its name in; `new_block` has no Template
    for a Run value.
  - Seeing a Run value's day before sending uses the Table notebook's "Try it" cell, or the
    Workflow notebook's last cell with `dry_run=True` added by hand.
  - The convert notebook's step 2 text and its decisions cell's comment (workflows.py) don't
    name Run values or "seed" yet; a Table reference's TAGS comment still says to answer with
    quotes after a function answers it.
- **The usability loop** gaining a scenario with Run values and a seed limit is the user's to
  decide (map, "Not yet specified"): not added.
