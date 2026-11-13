# The usability loop's memo per scenario

Type: task
Status: resolved
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

## Answer

Built 2026-11-13, in `tools/usability_loop.py` and `tools/usability_scenario_files.py`, with
tests in `tests/test_usability_loop.py` and the journey tests, and
`docs/usability-loop.md`'s "What a run is given, and what is cached".

- **Main by part.** `main_parts` hashes main's tree in four parts, each with the export's stamp
  left out:
  - `toolbox`: the Toolbox folder, whole;
  - `readme`: each `##` section of the README;
  - `how_tos`: each how-to of `how_to.html`, by its link;
  - `copilot`: each Copilot file.

  `inputs.json`'s `main` holds these and `named` in place of `tree`. It also holds `reads`, the
  scenario's list.
- **Each scenario's list.** `reads.json` sits beside `key.json`. It holds `readme` (headings),
  `how_tos` (links) and `copilot` (file names). The scenario builder writes it from
  `path_reads(...)`, and `read_scenario` reads it into `Scenario.reads`.
- **The hash.** `inputs_hashed_by_part` gives each part of the hash by what it is, such as
  `README section "The Workflows"` or `the Toolbox folder`, with that part's hash. The parts
  are:
  - the Toolbox folder;
  - the listed sections, how-tos and Copilot files;
  - `named`;
  - each file of `project`, the warehouse, each file of `scenario_files`, each phase and each
    loop file;
  - the list itself.

  `inputs_hash` is one hash of that.
- **plan.** When no run was recorded with these inputs, `plan` compares them with the last
  recorded run's kept `inputs.json`, in `.scratch/usability-loop/runs/`. It adds `; changed
  since its last run, <run>: <each part>`.
- **Missing names.** `prepare` and `plan` refuse a list naming a section, how-to or Copilot
  file main hasn't. `test_every_name_a_scenario_lists_is_on_main` holds all 14 lists to a
  main built from dev's commit.
- **Runs recorded before this ticket.** Their rows name a hash of the old shape, which no
  hash matches now, so `plan` says "run it". When their `inputs.json` is kept, it adds that
  the last run was recorded with main's whole tree as one input.
  `test_runs_recorded_with_mains_whole_tree_are_run_again_never_memoized` holds both.

Decisions:

- **Decided:** in main, the how-tos are one page inside the Toolbox folder,
  `sqlglot_composer/how_to.html`. The Toolbox part leaves out that page's how-to entries (each
  `<section class="entry">`), which are hashed one by one. It keeps the page around them, so a
  change to the page's script or head runs every scenario. Without this, every how-to edit
  would change the Toolbox hash and run every scenario, as before. `examples.html` stays in
  the Toolbox part. Ticket 13 moves the pages to main's `docs/`, and `HOW_TO_PAGE` moves with
  them. The test of the lists fails until it does.
- **Decided:** `named` no longer holds `.github/README.md`. Every phase message names the
  README, so keeping it whole would run every scenario on any README change. It is hashed by
  section instead. Every other named file, such as `copilot/formula_workbook.xlsx`, stays as
  before.
- **Decided:** the README's part above its first `##` heading goes by its `#` title,
  `sqlglot Composer`. Every list includes it, since every agent starts at the README's top.
  Every list also includes Copilot file 00, since every question to Copilot opens with it.
- **Decided:** each scenario's list is my reading of its path. Workflow scenarios list:
  - the README's top, `1. Start a Project`, their own step and `The Workflows`;
  - their Workflow's how-tos;
  - their Workflow's Copilot files, from file 00's "Which file".

  The Excel scenarios also list `Have Copilot write it` and Copilot files 11, 12 and 15. A
  list too small would leave a scenario memoized on a change it reads. When a round's agents
  are seen reading something unlisted, add it in `usability_scenario_files.py` and build
  again.
- **Decided:** main's other files (`CHANGES.md`, `LICENSE`, `requirements.txt`, main's
  `example_projects/`) are in no scenario's hash unless a phase message names them. A version
  raise changes `version.txt` in the Toolbox folder, so the "To update" part H2 reads in
  `CHANGES.md` reruns everything anyway. W8's and H2's Projects come from dev's folders and
  are hashed as `project`.
- **Decided:** a list naming what main hasn't is refused at `prepare` and `plan`, not only
  held by the test. Without the refusal, a renamed section would silently drop out of the
  hash. The journey test prepares on an empty main tree, so it clears the list.
- **Decided:** `read_scenario` needs `reads.json` and refuses any kind but `readme`,
  `how_tos` and `copilot`, so a misspelt kind can't drop out of the hash.

## Code review

`code-review` against 89798750, with the ticket as spec (Standards and Spec sub-agents on
Sonnet).

Standards, no hard violation:

- **Type hints imprecise:** `main_parts` and `missing_reads` hinted `dict[str, object]`.
  Fixed to `dict[str, str | dict[str, str]]`. `inputs_of` and `inputs_hashed_by_part` keep
  `dict[str, object]` for `inputs.json`, a JSON value of several shapes. That is the hint the
  file had for it before.
- **Names:** `said` (the standard's own example of a vague name), `memo_parts`, `listed`,
  `others`, `planned`, `kept`, `old` and `new` are renamed. They are now `part_in_words`,
  `inputs_hashed_by_part`, `listed_reads`, `unknown_kinds`, `plan_line`, `kept_inputs`,
  `parts_then` and `parts_now`.
- **readme_sections hard to follow in one pass:** fixed. It splits by heading first, then
  names the top part by its title, or "the top" when there is none.
- **Duplicated Code** (W7's and H1's lists spread from CONVERT_READS): fixed. The convert
  lists are three named lists, and W7 and H1 call `path_reads` with one more Copilot file.
- **Data Clumps, Primitive Obsession, Shotgun Surgery** (the three kinds as string keys):
  answered. `READ_KINDS` is the one map the kinds come from, and `read_scenario` refuses
  others. A type for them would be machinery to study for three lists of names.
- **Divergent Change** (README and how-to parsing in the loop's file): answered. It is
  hashing what the loop gives an agent, which is this file's job since 8.6.

Spec:

- **"a change to the Toolbox folder runs them all", but a how-to edit doesn't:** this is the
  how-to page decision above. `docs/usability-loop.md` now says so plainly.
- **README left out of `named`:** answered, see Decisions.
- **Old results with no kept `inputs.json`:** answered. `plan` still says "run it: no run
  recorded with these inputs", which is the reason. Only the note naming the old shape needs
  the kept file.
- **path_reads always adds the README's top and file 00; `read_scenario` refuses unknown kinds
  and needs reads.json; `prepare` and `plan` refuse missing names:** answered, see
  Decisions.
- **A README with no `#` title would key its top as "":** fixed. It is "the top".
- **A nested `</section>` would cut a how-to short:** checked. The page's 31 sections nest
  none, as `tools/how_to_page.py` writes one per how-to.
- **Nothing checks a list against what a run really reads:** answered. The spec doesn't ask
  for it; see the Decision on each list.

No beginner reader. Nothing a beginner sees changed: only `tools/`, tests and a dev doc.
