# Beginner reader, ticket 19 (Toolbox 8.0, the docs and the Copilot files)

Run 2026-10-31 on the dev working tree after e7f0864. The reader edits nothing, so this file was
saved from its report. Advisory only: the user decides what changes.

**Read:** the README template's opening, steps 2, 6, 8 and 9, "The Workflows" and "Have Copilot
write it"; how-tos 9 and 29, in source and on how_to.html; Copilot files 00, 01, 07, 11 and 13;
and the Intermediate Example project's README.

**Ran:** how-to 9 in a temp folder, and the README's Excel path with two plain SELECT .hql
files in one batch.

## Stops

### The README template

1. **How do_next()'s rule reads:** "those that change only files with a call of their own".
2. **Step 2 and the refresh step:** step 1 already wrote the Database module, so why does a
   later step refresh it?
3. **`new_table`:** one name in step 6, a list in the Workflow.
4. **What makes a Workflow "started".**
5. **Scripts saved beside convert.ipynb, and copied into `<name>/scripts/`:** which copy is
   the real one?
6. **convert's call:** the step, the chart and the Excel chart each write it differently.
7. **"seed"** is used before it is said.
8. **Prod names after promote.**
9. **The charts:**
   - class names (`permission`, `fiddling`, `thing`) that don't match the list's words;
   - no legend;
   - edges written before their nodes.
10. **`#35;`** shows in the upgrade chart.
11. **No blank line between each list item and its call.** Under CommonMark the call runs into
    the sentence, its loops flattened.
12. **"Check first line"** is never said.
13. **Where `admin.check_the_copy` goes.**
14. **Two file steps that act differently:** do_next() runs new_table's but not upgrade's.
15. **Stuck: the Excel path.** A batch of several plain SELECT scripts, one per final Table as
    file 11 writes them, is refused.
16. **"Compare each with its original"** for a workbook, which has none.
17. **The batch named two ways in the Excel section:** "budget" and "sales_summary".
18. **Dev or prod names** in `project.promote([...])`.

### How-to 9

19. **The scripts are files to save, not steps to paste.**
20. **`database="ops"` passed,** though every table in the scripts names its database.
21. **Is mart dev or prod?**
22. **Outputs cut to `...`** in the source.
23. **Stuck: the page sends you to mart.fail_history.** It stayed whole Hive, unchecked_hive,
    though the page promises its clauses.
24. **The checklists' "Send the original's SET lines" box:** an action no step performs, which
    the page ticks.
25. **What a location= is.**
26. **Why the seed needs dynamic_partitions.**
27. **The compare's four lines,** one read differently.

### How-to 29 and how_to.html

28. **Six charts shown as raw Mermaid text.**
29. **"finding the Project".**
30. **A decision step with a call.**
31. **"no file tells of".**
32. **The escaped quotes** in the source.

### The Copilot files

33. **07 or 13 to convert?**
34. **The shared rules' list of files stops at 12.**
35. **07 points to 13's cells,** which a chat holding only 07 hasn't got.
36. **07's long Conversion sentence.**
37. **`hive_settings("converted", ...)`.**
38. **11 asks for Python,** which the Conversion writes.
39. **The upgrade step's wording.**
40. **`file=` and `files=`.**
41. **13's worked example passes None** where its step passes HIVE.
42. **"no file tells of".**
43. **13's names list is short of the steps' calls.**

### The Intermediate Example project's README

44. **How its compare passed,** when how-to 9's fails.
45. **Which opt-out was kept.**
46. **convert's call cut to `...`.**

**Costliest:** 15 (the Excel path); 23 with 24 (how-to 9's notebook and boxes); 9 to 11 with
28 (the charts as a beginner meets them).

## What was done

See ticket 19's "Beginner reader" section.
