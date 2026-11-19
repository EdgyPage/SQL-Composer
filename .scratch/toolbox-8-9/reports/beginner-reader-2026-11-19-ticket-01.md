# Beginner reader, 2026-11-19: ticket 01's `copilot/workbook_text.py`

Read: the script's module docstring and its refusal when the reader can't be found, against the
script at 14fcce24. Advisory; the user decides what changes.

## Stops

1. **"in the folder beside this one"**: this script, or the copilot folder? And no line says
   to keep the sqlglot_composer folder there.
2. **"the way the convert Workflow reads it"**: a person on the Copilot path may never have met
   the convert Workflow.
3. **"It needs nothing but Python"**: read as "the script works alone", true before, not now.
   Nothing needs installing, but the folder is needed.
4. **The refusal's "Usual fix"**: "run it from the download's top folder" fixes nothing. The
   script looks for the folder beside its own folder, not where it is run from, and it didn't
   say the path it looked in.

## Fixed (errors), 2026-11-19

- Stop 4: the refusal names the path it looked in and says to put the download's
  sqlglot_composer folder there, beside the copilot folder; nothing needs installing. Its test
  holds the path.
- Stops 1 to 3: the docstring says to keep the sqlglot_composer folder beside the copilot
  folder that holds the script, drops the convert Workflow, and says "nothing installed but
  Python".
