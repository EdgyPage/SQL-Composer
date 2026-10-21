# Hints on the public functions

Type: task
Status: claimed
Blocked by: 02
Size: M

## Question

The Toolbox's public functions, the names in `public.__all__`, `admin.__all__` and
`project.__all__`, have no hints; `help()` prints their signatures to the beginner. They get
hints in the map's plain style.

Asked which classes the public signatures name should be public too, the user (2026-10-21) chose
`Clause` and `Window`, already glossary words, which a Building block gives back; `Named`,
`Ordering`, `Subtotals` and `TableLogic` are named in `help()` as they are, not public.

## Done when

- `Clause` and `Window` are public names (96 in all), each with a docstring whose example runs,
  in CONTEXT.md and CHANGES.md as ticket 01's five are.
- Every public function and public class's methods hint each argument and its return.
- What `help()` shows reads plainly: the beginner reader reads the signatures as `help()` prints
  them, and its stops go to the user, who decides.
- The pytest run passes, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).
