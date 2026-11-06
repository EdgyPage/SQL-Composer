# Ticket 12: the beginner reader's report

Run 2026-11-05 by `.claude/agents/beginner-reader.md` (opus), on ticket 12's uncommitted docs:
the 8.4 docstrings (run_value, tag_text, latest_partition, hive_date, today, script_tag,
seed_copy, project.write_decisions), how-tos 09, 28 and 29, the README template's section 9 and
Update, CHANGES.md's 8.4, and Copilot files 17, 07, 10, 13, 16 and 00. Line numbers are of the
files as the reader saw them, before the fixes. What was done with each stop is in the ticket's
Answer.

Beginner read of 8.4's docs. I read everything you listed, in order, and edited nothing. I looked
in CONTEXT.md twice, for "dynamic Partitions" (it isn't there) and "Run value"; both count as
stops below. One note first: `sqlglot_composer/version.txt` still says 8.3, so Copilot file 17's
header ("sqlglot Composer 8.3") and how-to 28's printed "Upgraded ... to 8.3" contradict the
"converted before 8.4" wording around them. That is the version item, which is yours to decide.

## Stops

### Docstrings

1. `sqlglot_composer/run_values.py:131-138` (run_value), "The Statement's lineage draws a box for
   it, naming the function, what it was given and what it gave, with an arrow into it from each
   table the Toolbox read for it while it ran ...". One sentence carries four ideas, and the
   lineage part isn't needed to use the function. A reread. Short fix: split it, lineage last.
2. `run_values.py:218-219` (tag_text), "for a bare one in Hive kept whole, which stands for Hive,
   its value's own quotes and all". I couldn't tell when I would call `quoted=False`. Stuck for
   a while. Short fix: one plain if/then line for each of the two cases.
3. `run_values.py:293` (latest_partition example), `def period_end():` has no
   `-> datetime.date`, yet how-to 09 gives `run_day` one. A moment. Short fix; standards.md
   requires hints in code a user copies.
4. `run_values.py:360`, "which script_tag writes so". "So" means "in that form". A moment. Short
   fix.
5. `conditions.py:31`, "as last_n_days sees it". I had to guess why today is tied to
   last_n_days. A moment. Short fix.
6. `unchecked.py:418-419` (seed_copy) and how-to 09 line 519, "a value, that value or later". I
   expected `{"dt": "2026-09-01"}` to mean that one Partition only, the way a list means only
   those values. A reread, and an easy mistake to make in use. Bigger than wording: either the
   meaning changes, or every place it appears gets a bold warning.
7. `project.py:3567-3611` (write_decisions). Forty lines of unbroken prose. The all_tables
   paragraph alone defines `tables`, three Workflows' cells, location_root, the overwrite order
   and the refusals. A reread, close to stuck. Bigger: it needs restructuring into short
   paragraphs or bullets, not a word swap.

### How-to 09

8. Lines 316 and 322 against line 246. Step 8's goal is "so no day is typed in", but the Hive
   shows `PARTITION(dt = '2026-09-24')` typed in, and only the WHERE follows run_day. So
   tomorrow's rows would overwrite the 2026-09-24 Partition. I couldn't tell whether I had
   misread or the example is wrong. Stuck. Bigger: the example, or what a Conversion does with
   a typed PARTITION, needs addressing. At the least, one sentence saying the PARTITION stays as
   the script typed it, and what to do about it.
9. Line 206, "so step 10 seeds it". Seeding is step 11 (step 10 is create). This line is new in
   8.4. A reread. Short fix.
10. Two step numberings: line 273 "Run the Workflow's step 3 cell again, as in step 7", line 334
    "The Workflow's steps 4 to 6", line 347 "The Workflow's step 5", line 429 "left unwritten by
    step 3", line 530 "step 3's report". The page's steps and the notebook's steps share
    numbers, and I had to work out which was meant each time. A reread at each one. Mostly a
    short fix: always name the notebook's as "the notebook's step N".
11. Line 247-248, "until you answer it again, where the scheduler put a new day there each
    night". "Where" means "whereas". A reread. Short fix.
12. Lines 292-295, "run again, an answer it wrote before is no change", and "with the call that
    registers it, the Project's list of what it holds". Garbled grammar, and registering is a
    second action hidden inside step 8. A reread. Short fix for the grammar; make the register
    call a step of its own.
13. Line 172-174 (and README line 650), "each answer still to give "<FILL IN>"". It took a
    reread to see it means "each answer not yet given shows <FILL IN>". Short fix.
14. Line 349, "Session settings for dynamic Partitions". This term isn't defined anywhere,
    CONTEXT.md included. A lookup. Short fix: one clause.
15. Line 353, `seeded=True`. I had to guess it means "only the tables that have a seed". A
    moment. Short fix.
16. Lines 410-411 (and Copilot 16's new lines), "its seed copies every Partition until you
    answer "seed" for it in the promote notebook". Run values carry over to prod but seed limits
    don't, and nothing says why. A reread. Short fix: give the reason.
17. Lines 425-427, "two tables answered with one function each call it". The grammar of "each
    call it" stopped me. A reread. Short fix.
18. Lines 435-437, "a date a function gives with no quotes, 2026-09-24, since the quotes are the
    original's". A reread. Short fix.
19. Line 449, `run_value(days_before, run_day(), 1)`. A few lines later, Common mistakes says
    "never `run_day()`". It only works here because it's an argument to run_value, and the page
    never says so. A moment. Short fix.
20. Lines 416-530. "Run values, in full", "all_tables, in full" and "Seed limits, in full" are
    reference material, but they sit as `###` sections inside `## Steps`, after step 14 has
    already said "Then check it worked, below". instruction-rules.md puts reference under `##`
    headings. A moment. Short fix: move them.

### How-to 28, how-to 29, the README

21. How-to 28, lines 22-25, "A Project 8.3 or any later version wrote upgrades straight to the
    newest ... One 7.1 to 8.2 wrote upgrades the same way". The word "that" is missing ("a
    Project that 8.3 wrote"), and "hold the result to the newest's" is about tests, not what I
    do. A reread. Short fix. The same garble is in CHANGES.md line 13-14, "a Project 8.3 or
    later wrote upgrades straight to the newest Toolbox".
22. How-to 29, line 102, "An answer is text, such as a folder ... or a Run value's function". A
    key is a list or None, and types are a dict. A moment. Short fix.
23. README line 616, "is read past where a value goes". "Read past" is jargon. A moment. Short
    fix.
24. README lines 655-663. One decision-rule bullet defines the Run value, says where to write
    it, how to import it, how to preview it and how to register it. Registering is an action
    buried in a rule. A reread. Short fix: move registering into a step.
25. README line 671, "run step 5's steps again: write the answers in, write each table, and
    compare each". It leaves out create and seed. Do I re-seed? A moment. Short fix.
26. README lines 1404-1405, "such as upgrade_8.4.md: its last line names each". "Its" could be
    the checklist or the upgrade's report. A moment. Short fix.

### CHANGES.md

27. CHANGES.md lines 31-34, last_n_days now counting from UTC. This is a behaviour change, and
    the fix is "bound the read in its place with `run_value(...)` of a function of yours that
    starts from `today(utc_offset_hours=-6)`". There is no example, and a beginner has to put
    together `at_least(col, run_value(fn))` alone. A reread, close to stuck. Moderate: add a
    three-line example.

### Copilot files

28. Copilot 17, line 43, "3. **Write the decisions cell**: ... then step 3's cell. Then step 4."
    The file's own step 3 and the notebook's step 3 collide, and again at lines 58, 60 and 82. A
    reread. Short fix: "the notebook's step 3 cell". The steps also lack a goal and a "done
    when", which instruction-rules.md asks for.
29. Copilot 17, line 41, "taking no argument". run_value's functions do take arguments; the
    rule only holds for answers to a tag. A moment. Short fix.
30. Copilot 17, lines 53-54, "`today(utc_offset_hours=-6)`, the user's offset, UTC with none". A
    reread. Short fix.
31. Copilot 17, lines 126-128, "team_log's seed only from 2026-09-01, by its day, and its US and
    CA teams". A reread. Short fix.
32. Copilot 10, new line, "`${hivevar:x}` is Hive as written, braces not doubled". I hadn't
    heard of doubling braces, so the warning made no sense. A moment. Short fix: say it is about
    `{dt}`-style placeholders.
33. A glossary mismatch across the docs. CONTEXT.md line 168 and Copilot 17 line 20 define a Run
    value as the *value* a function gives. README line 655, how-to 09 line 26 and CHANGES line 8
    say "a Run value, a function of yours". Elsewhere the wording is "a Run value's function". I
    had to look it up to know which thing the word names. A lookup. Short fix, but it touches
    many files: pick "a Run value's function" for the function everywhere.

## The three costliest stops

1. **How-to 09, PARTITION typed in while the WHERE uses run_day** (stops 8 and 9). It
   contradicts step 8's own goal, would overwrite the wrong Partition each night, and the wrong
   step number nearby adds to the doubt. Bigger than wording.
2. **write_decisions' docstring** (stop 7), with the same density in "all_tables, in full". It
   is the one function every answer goes through, and its help() is a wall. Bigger: it needs
   restructuring.
3. **Two step numberings** (stops 10 and 28): how-to 09 against the notebook, and Copilot 17's
   steps against "step 3's cell". It costs a reread at every cross-reference. A short wording
   fix, applied consistently.

Next in line: the seed's "single value = that value or later" meaning (stop 6, bigger) and Run
value meaning both the function and the value (stop 33, wording).
