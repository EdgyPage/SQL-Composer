# The usability round

Type: task
Status: open
Blocked by: 12
Size: M

## Question

Can a zero-context user schedule a run from what main ships?

## Done when

- **Inputs recorded and memoized** (the user, 2026-11-09: "start documenting and memoizing
  the inputs ... so we can reduce token counts and speed up test times"):
  - each run writes `_loop/inputs.json`: the scenario, dev's commit, a hash of each file of
    main's tree the scenario's phases name or the run reads, the scenario's own files, and
    each phase message, and the row in results.md names that hash;
  - `prepare` builds main's tree once per commit into a cache in the loop's temp folder and
    copies it, and sets up a scenario's warehouse once per (commit, scenario);
  - a scenario whose inputs hash matches a run that passed is reported as memoized, with that
    run named, and isn't given to an agent again unless asked (`--fresh`);
  - `tests/test_usability_loop.py` builds main's tree once per session, not per test;
  - `docs/usability-loop.md` says what is cached, where, and how to clear it.
- A scenario in `tools/usability_scenario_files.py`: from the intermediate Project, a run of a
  table's weekly breakdown, parameters given as text, run top to bottom.
- A round of it and W1, three runs each, on 8.6 as it ships, recorded in results.md with what
  it found.

## Answer
