# The edition seam

Type: task
Status: open
Blocked by: -
Size: M

## Question

Add `edition.py` as a shared file (still generated into spark_composer/ by swap()), holding the
Edition's folder, product, version and Toolbox folders, the plugged-in writing and engine, one
forwarder per EDITION_INTERFACE function, and `plug(...)`, which refuses a second, different
Edition in one Python. Reroute every shared file's `from .writing import` and `from . import
engine` through it; lineage reads the version through `edition`, and its time, commit and
version through one small function each, so a tool can pin them; tables.py and running.py name
the Edition folder from `edition.FOLDER`; warn_at_callers_line skips frames in every Toolbox
folder.

## Done when

- The goldens and both galleries are byte-identical after regenerating.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).
