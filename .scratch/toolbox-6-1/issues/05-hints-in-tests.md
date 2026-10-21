# Hints in tests

Type: task
Status: open
Blocked by: -
Size: L

## Question

`tests/` is partly hinted: about 400 functions are partial and 107 bare. Every test returns
`-> None`; fixtures and helpers hint their arguments and returns (`tmp_path: Path`,
`monkeypatch: pytest.MonkeyPatch`).

## Done when

- Every function in `tests/` hints each argument and its return, checked with an `ast` count.
- No test changes what it checks.
- The pytest run passes, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).
