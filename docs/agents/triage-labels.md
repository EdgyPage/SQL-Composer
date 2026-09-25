# Triage Labels

The skills speak in five canonical triage roles. This maps them to the strings used here.

| Label in mattpocock/skills | Label in our tracker | Meaning                                  |
| -------------------------- | -------------------- | ---------------------------------------- |
| `needs-triage`             | `needs-triage`       | Maintainer needs to evaluate this issue  |
| `needs-info`               | `needs-info`         | Waiting on reporter for more information |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human`    | Requires human implementation            |
| `wontfix`                  | `wontfix`            | Will not be actioned                     |

This tracker is local markdown, so a "label" is the `Status:` line near the top of the issue file
(see `issue-tracker.md`), not a tracker-side object. Wayfinder tickets use `open` / `claimed` /
`resolved` on the same line.
