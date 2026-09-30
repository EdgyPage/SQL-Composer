# CHANGES 3.0, a draft

Ticket 26 of the PySpark work writes these lines into `CHANGES.md` when 3.0 ships, in both
folders. Like `CHANGES.md` itself, they name neither folder, since both folders ship it as it is.
Each ticket that changes what a user sees adds its line here as it goes. A change that ships in
a 2.1 re-export goes into `CHANGES.md` under 2.1 instead.

- **An object from the other Edition's folder is refused plainly** (ticket 23). Given, say, a
  Table reference whose file imports the other folder, each function says which folder made
  the object, and how to import from one folder only, whichever your notebook uses.
