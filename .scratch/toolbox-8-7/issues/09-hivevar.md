# Hivevar

Type: task
Status: open
Blocked by: -
Size: L

## Question

The user's SQL comes with values built in, and they want to load other values at run time
without the Toolbox. The user's words: "I want the script tag behavior to remain the same and
be able to be written over by some mechanism with the capability to replace hivevars at
runtime. please don't revisit the script behavior" (Q7, Q12, Q13, Q20).

## Done when

- **The Script tag stays as it is.** It's read, converted and answered as Decisions just as in
  8.6. No test of Script tags changes.
- **A new public `hivevar(name, default=)`** is one more answer to a tag, beside text and a Run
  value function. `default=` takes text, as `"'2026-10-31'"`, or a Run value function.
- **In the Hive,** `'${hivevar:NAME}'` stands where the tag stood, quoted as the tag stood; a
  bare tag's Hivevar stands bare.
- **When the Toolbox sends a Statement** with Hivevars (`run_execute`, `run_tables`,
  `built.run`), it first sends `SET hivevar:NAME=<value>` for each, as it sends Session
  settings.
  - The value is the default, or a Run value default's result.
  - The dry run and the lineage show the `SET` lines.
- **A Scheduled run overrides one by name,** `build_run(..., hivevars={"NAME": value})`.
  - A name no Statement uses is refused, naming those it does.
  - A parameter may give the value, as `run_values=` takes one.
- **On export** (`export_hive`, `export_run_hive`), no `SET hivevar` line goes in the Hive.
  Instead, a `<name>.hivevars` file beside the `.hql` holds `--hivevar NAME=value`, one per
  line, the defaults as they were worked out at export.
  - Its header says why: Hive lets a `SET` in the script beat a value given on the command
    line.
- **In the convert notebook,** a tag's Decision can be answered `hivevar(...)`, and the
  README's Script tag steps say how. Copilot file 07 names it.
- **The lineage** draws a Hivevar as a value with its name and default.
- **CONTEXT.md's Hivevar entry** matches what was built.
