# Instruction rules: how every doc a person or Copilot follows is written

From Microsoft Learn, "Write effective instructions for declarative agents" (Microsoft 365
Copilot extensibility, updated 2026-10-27), read 2026-11-01, as this repo applies it. It binds
each Copilot file in `copilot/` (written from `tools/copilot_sources/`), the README template
(`docs/clean-branch-readme.md`), the how-tos (`worked_examples/how_to/`), the Formula workbook's
Steps sheet (`tools/formula_workbook.py`) and the text cells of the notebooks the Toolbox writes.
The code reviewer and the beginner reader read docs against it.

## The shape of a doc

- **Sections, then steps.** Group what is reference under `##` headings, as bullets, in no
  order. Number only what must be done in order: a workflow. Use one list type per list.
- **A step is atomic and has three parts:** its goal, the action, and the transition, the
  check that says it is done and which step comes next. One action per step: "map the
  workbook" and "write the Hive" are two steps, never one.
- **Decision rules are explicit if/then lines**, one branch per line, covering every case the
  doc's task meets, so no reader blends two branches or picks one by guess: "If a Table is
  read by a formula or a query, it is a step. If a query loads it too, it is also a final."
- **An output contract** fixes what the reply or result holds and in what order: its parts,
  each part's format, and what it leaves out.
- **Examples:** more than one where the task is not simple, each showing a different case or
  edge, such as a query that is both read and loaded, beside the plain case.
- **Terms defined where they are used:** each word of this repo's own, such as Table
  reference or step, is defined in the doc, as `CONTEXT.md` defines it, the first time it
  appears.
- **A final self-check** closes every doc with steps: a short list of checks, each observable
  in the answer ("each Power Query the workbook lists is named in the map"), not a wish ("be
  thorough").

## The wording

- **Say what to do**, in the positive: "write NULL in its place", not "don't drop the
  column". A prohibition stays only as a hard guardrail, paired with the positive target.
- **Precise verbs:** read, write, name, list, check, ask, save, run; not "handle", "process" or
  "deal with".
- **Literal:** a doc that a model follows starts with a short header saying to follow its
  steps in order, as written, with nothing added.
- **Names in backticks**, such as `project.convert` and `<database>`; the one or two rules
  that matter most in bold.
- **Markdown structure:** `#`, `##` and `###` headings; `-` for bullets, `1.` for steps; no
  list nested more than two levels.

## For Copilot files alone

- Each file is at most 8,000 characters, as `copilot/count_characters.py` counts, and stands
  alone, since a person loads only the files the task needs.
- A file a person loads beside others says which others, and once, what each is for.
