# Ticket 12: the beginner reader on the admin layout

Run 2026-10-31 on commit 3ad1c24 (opus), reading the README template's Project table and Update,
how-to 01's file list, how-to 28, `project.do_next` and `project.upgrade`'s docstrings, the
notebooks a new Project gets, `admin/databases.py`, and CHANGES.md's 8.0. It ran `start`,
`check` and `do_next` in a scratch Project. Its stops, in reading order, with what was done.

| # | Where | The stop | Done |
|---|---|---|---|
| 1 | README Project table | "Workflow" is never defined in the README; when to use a Workflow notebook over the plain call | Left for ticket 19, which starts each README job from its Workflow notebook |
| 2 | README Project table | "its notebook's first cell" is the third cell; saving before `do_next` is said only in its docstring | "names cell"; the row and the notebook say to save it |
| 3 | README Project table | what reads `databases.py`, what to put there on the Example database | Left for ticket 13, the first that reads `DEV` |
| 4 | README Project table | does `run_tables` add a row to `sent.csv` | It does, through `run_execute`; the row and CHANGES say so |
| 5 | README Conversion step 5 | `HIVE = ''` and the call's `database=` differ from the text | The step names the notebook's `project.convert(...)` cell; HIVE is None until filled |
| 6 | README Update step 5 | the upgrade notebook "once your Project has one" though `start()` writes it | Says `start()` writes it and an Upgrade adds it |
| 7 | README Update step 5 | Update against Upgrade buried mid-step | Left for ticket 19 |
| 8 | How-to 01 | `admin/workflows/references/` against the top `references/` | Left: the Workflow's name; ticket 19 |
| 9 | How-to 01 | `DEV` and `PROD` never filled in | Ticket 13 |
| 10 | How-to 01 | "each send of a change": "send" is avoided | "each change you run on the warehouse" |
| 11 | How-to 01 | `.parents[2]` counted by hand | Left: it says "three down" |
| 12 | How-to 28 | "before taking the version file out", though the page rewrites it | Says "before writing 7.2 in the version file" |
| 13 | How-to 28 | why new_block is written again | Left: the checklist line says "rewrote"; CHANGES says why |
| 14 | How-to 28 | the archiving of a real 7.2 Project's notebooks isn't shown | Left: CHANGES's "To update from 7.2" lists it |
| 15 | `check` docstring | doesn't name the Workflows' next steps | Names them |
| 16 | `do_next` docstring | `project.new_table(TABLES)`; ", a decision" reads as part of the title | Calls are written out with the names; "It is a decision, yours to make" |
| 18 | `databases.py` | nothing reads it; `PROD = "mart"` clashes with the tutorial's tables | Ticket 13 |
| 19 | `new_table.ipynb` | "first cell" | "names cell" |
| 20 | `new_table.ipynb` | run the step cells or `do_next()`? | The notebook says: each step's cell in turn, or `do_next()` for the file steps |
| 21 | `new_table.ipynb` | "A permission." is in no doc | Each step says its kind in words: "It is a call to the warehouse, yours to run" |
| 22 | `new_table.ipynb` | "in dev" doesn't match the call | Ticket 13 |
| 23-24 | `convert.ipynb` | no triple quotes; FILE never passed | HIVE and FILE are None until filled, and the call passes `file=FILE` |
| 25 | `convert.ipynb` | `compare_with_original(...)` and `run_tables` raise NameError | Compare is in the Conversion's notebook; `project.run_tables(tables=[TABLE], ...)`; the first cell imports `admin`, `run_execute` and `show_hive` too (D317) |
| 26 | `convert.ipynb` | dense headings; scripts against one query | Left: convert is rebuilt in tickets 13 to 16 |
| 27 | `remove.ipynb` | "first cell" | "the cell below" |
| 29 | `upgrade.ipynb` | says to fill in a first cell it lacks; `do_next` skips it | A Workflow with no inputs has neither the fill-in text nor a `do_next()` cell |
| 30-32 | CHANGES 8.0 | "dev"; `"your_name"`; "its kind" | "its kind (such as write)"; the rest left for ticket 20, which finishes the section |

Stops 17 and 28 were not stops.
