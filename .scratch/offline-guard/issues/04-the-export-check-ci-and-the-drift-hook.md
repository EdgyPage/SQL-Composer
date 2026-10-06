# The export check ci and the drift hook

Type: task
Status: open
Blocked by: 01
Size: S

## Question

Plan steps 6, 7 and 8: the export refuses a Clean tree with a finding; dev.yml gets `permissions: contents: read` and SHA-pinned actions; drift_list sanitises file paths it prints into Claude's context.

## Done when

- A spoiled template stops the export; CI's four jobs pass; a crafted path prints safely.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).
