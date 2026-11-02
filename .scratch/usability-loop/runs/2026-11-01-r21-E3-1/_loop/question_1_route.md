You are standing in for Microsoft Copilot in a web chat. Use no tools: answer from what is written here and what you already know.

The user pasted this as their first message:

<<<
# Copilot files for sqlglot Composer 8.2: start here

**Read this file to choose the one Copilot file your task needs, then follow the steps below
in order.**

sqlglot Composer 8.2 writes Hive, the SQL of the user's warehouse, from Python. You build a Statement from Clause functions, such as
SELECT, FROM and WHERE, and the Toolbox writes its Hive and refuses one that would give a
wrong number or read too much. These files teach Microsoft Copilot to write that Python, so
you can ask it in plain words.

## Terms

- **Copilot file**: one of the files in this folder; each teaches Copilot one objective.
- **Statement**: one query, built in Python with `statement(...)`, that becomes one string of
  Hive.
- **Project**: your folder at work holding the Toolbox and your own code.
- **Table reference**: the file in your Project's references/ folder that describes one
  table: its columns and their types, its partitions and its Key.
- **Saved table**: a table in the warehouse that your own Statements write.
- **Refusal**: the Toolbox's message when it won't write a Statement's Hive.
- **Workflow**: the steps to one end goal, such as converting Hive, each a cell of the
  Workflow's notebook in admin/workflows/.

## Steps

1. **Choose the file.** Goal: the file that teaches Copilot your task. Action: find your
   task under Which file. Done when you have one file, or for an Excel workbook three, as
   the Decision rules say. Then step 2.
2. **Open a chat.** Goal: a chat holding nothing from another task. Action: open a new chat
   in Copilot. Done when the chat is empty. Then step 3.
3. **Load the file.** Goal: Copilot reads the file first. Action: paste the file as your
   first message, and send it. If a paste is cut short, attach the file instead. Done when
   Copilot has the file. Then step 4.
4. **Ask.** Goal: Copilot knows your tables. Action: say which tables to read: paste each
   one's Table reference, its file in your Project's references/ folder, or say its import
   line and columns, such as: `from references.ops__job_runs import job_runs` gives
   ops.job_runs: run_id bigint, job_id bigint, status string, dt string; partitioned by dt;
   Key run_id. Done when Copilot answers with code. Then step 5.
5. **Run it.** Goal: the code works in your notebook. Action: run what Copilot gives. Done
   when it runs. If the Toolbox refuses it, step 6.
6. **Fix a refusal.** Goal: code the Toolbox takes. Action: start a new chat with file 09,
   paste the code and the whole message, and ask for the fix. Done when Copilot answers
   with the fixed code. Then step 5.

## Decision rules

- If the Toolbox refused your code, load file 09.
- If your task is to convert an Excel workbook, attach files 15, 11 and 12 (or paste
  each as a message of its own), then attach the workbook and ask Copilot to convert
  it: a chat holds one file at a time, but for this one task.
- If you want a query of Hive someone else wrote as Toolbox code, load file 07. If you want
  their Hive made into Saved tables in your Project, end to end, load file 13.
- Otherwise, load the one file whose line under Which file names your task.
- If you want something else after a task, start a new chat with that task's file.

## Which file

- `01_imports_and_project.txt`: start a Project, import the Toolbox, your Table
  references and warehouse.py's query and execute, and run a Statement.
- `02_table_references.txt`: describe a table: add its Table reference, or write one by
  hand for a Saved table, with its columns, partitions and Key; check its Key.
- `03_build_a_statement.txt`: read rows: pick columns, filter, count, add up, group, sort,
  and build in steps with Derived tables.
- `04_joins.txt`: combine tables with JOIN, LEFT_JOIN and the others.
- `05_windows_and_subtotals.txt`: a rank or row number in each group, the latest row or top N
  of each group, the row before, running totals; subtotals; stacking Statements.
- `06_save_a_table.txt`: write a Saved table: its Table notebook's logic cell, with
  create(), rows(), preview() and write().
- `07_convert_hive.txt`: turn Hive someone else wrote into Toolbox code.
- `08_check_and_compare.txt`: compare a Statement with the Hive it replaces, check a Key, see
  what is left to do in the Project, follow lineage.
- `09_fix_a_refusal.txt`: fix code the Toolbox refused.
- `10_hand_written_hive_and_functions.txt`: labels from a lookup or a chain of if/else,
  Hive functions the Toolbox doesn't wrap, Hive written by hand, and upkeep of a table.
- `11_excel_formula_workbooks.txt`: each formula of a Formula workbook, an Excel workbook
  laid out as `formula_workbook.xlsx` shows, as Hive; loaded with files 15 and 12.
- `12_excel_power_query.txt`: the same workbook's Power Query, whole-column totals and Total
  Rows as Hive; loaded with files 15 and 11.
- `13_workflows.txt`: converting Hive and promoting it to prod, a whole job step by step,
  from its Workflow notebook in admin/workflows/.
- `14_workflows_new_tables_and_upkeep.txt`: a new Saved table, from a query or by hand,
  Table references, an upgrade, a change to a Saved table, each a whole job step by step.
- `15_excel_workbook_steps.txt`: turn a Formula workbook into Hive, step by step: which
  Tables and queries become which queries, and the reply; loaded with files 11 and 12.

## Fitting Copilot

- Copilot takes at most 8,000 characters at once, spaces and line breaks included, and each
  file fits.
- Edit a copy if you like, then count it from the download's top folder:
  `python copilot/count_characters.py my_copy.txt` says how many characters it holds and
  whether it fits.

## Self-check

- The chat is new, and its first message is the file your task's line names (for an Excel
  workbook, files 15, 11 and 12).
- Your question names each table to read, by its Table reference or its import line and
  columns.
- For a refusal, the new chat holds file 09, your code and the whole message.

>>>

Then asked:

Please convert this Formula workbook into Hive, following Copilot files 15, 11 and 12, and reply with the Map and the Hive. Its job_runs sample is copied from ops.job_runs, so write ops.job_runs for it. I need only the final daily_runs (the Daily summary) as a table; its Total Row is not needed as a table, so leave that final out.

Reply with the one Copilot file the user should load next, such as 07_convert_hive.txt, and nothing else.
Write your reply under one heading, `## Q1`.
