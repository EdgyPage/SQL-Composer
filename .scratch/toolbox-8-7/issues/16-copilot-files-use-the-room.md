# The Copilot files use the room

Type: task
Status: open
Blocked by: -
Size: L

## Question

The user raised each Copilot file's limit from 8,000 to 9,000 characters (dev 257d9724), then
asked: "Make the documentation more robust if it can use the characters." Each file has about
900 to 1,800 characters to spare. What should each one add, so Copilot gets more right?

## Done when

- **Each Copilot file's source** (`tools/copilot_sources/`) adds what Copilot has been missing,
  drawn from the evidence, not guessed:
  - the Copilot evaluation's misses (`.scratch/copilot-eval/results.md`,
    `excel-files-11-12-misses.md`, the kept replies in `.scratch/copilot-eval/memo/`);
  - the usability rounds' findings about the Copilot files (`.scratch/usability-loop/results.md`,
    the "Found in ..." sections), such as file 18 never naming `write_days` for a chosen period;
  - the beginner readers' points on the files (`.scratch/toolbox-8-7/reports/`, and file 19's
    four points and the code review's two in ticket 11's Answer);
  - names a file's objective uses but its names list leaves out.
- Each file stays at or under 8,800 characters in both counts, keeping 200 to spare.
- Every Python block in each file still runs, and every name is public (the existing tests).
- `tools/copilot_files.py`'s refusal says "over the 9,000 each Copilot file keeps to", not
  "Copilot takes" (from the drift review of 7c17daf).
- **The evaluations run again** on the new files version, with ticket 02's memo:
  - the Copilot evaluation's arm C on the dev split, on Haiku, then the held-out split once;
  - the Excel evaluation for files 11, 12 and 15;
  - ticket 11's Metric request evaluation for file 19.

  Each scores at least as well as its last recorded round, recorded in `results.md`. A drop is
  fixed or reported with the reason.
- The beginner reader reads a sample of the changed files, and its report is linked here.
