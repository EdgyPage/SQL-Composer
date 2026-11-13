# The usability loop's memo per scenario

Type: task
Status: open
Blocked by: -
Size: M

## Question

Today a scenario's `inputs_hash` holds one hash of main's whole tree, so any change to main
runs every scenario again (Q11a). What does each scenario actually read, and how is it keyed on
only that?

## Done when

- `_loop/inputs.json`'s `main` holds, in place of `tree`:
  - the Toolbox folder, hashed whole;
  - the README, one hash per `##` section;
  - each how-to and Copilot file, on its own;
  - each file the phase messages name, as `named` does now.
- Each scenario names what its path reads, in its folder beside its answer key:
  - the README sections, by heading;
  - the how-tos and the Copilot files.

  Its `inputs_hash` is made from those, plus the Toolbox folder, the rest of `inputs.json`
  (`project`, `warehouse`, `scenario_files`, `phases`, `loop_files`) and that list itself.
- A test holds that every name in a scenario's list exists on main, so a renamed section or
  file can't leave a scenario memoized on nothing.
- `plan` names, for each scenario it says to run, which of its inputs changed.
- A change to a README section no scenario lists runs no scenario again; a change to the
  Toolbox folder runs them all.
- `docs/usability-loop.md`'s "What a run is given, and what is cached" says so.
- Results recorded before this ticket, which hold the old hash, are read as "run it" once,
  never as memoized.
