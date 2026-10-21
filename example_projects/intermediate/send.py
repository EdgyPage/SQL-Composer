# sqlglot Composer 6.0, exported 2026-10-21 07:05 - copy it, then edit your copy
"""send - runs a Hive string on your warehouse and gives back a pandas DataFrame.

Why: every notebook in the Project sends its Statements through this one function, so a change
to how you reach the warehouse is made here, once.

Replace example_database.send(hive) with your warehouse's call: how-to 1, Start a Project,
shows how to write it. It imports none of your own files, so any notebook or script of yours
can import it.
"""

from sqlglot_composer import example_database


def send(hive):
    """Run a Hive string and give back a pandas DataFrame."""
    return example_database.send(hive)  # at work: your warehouse's call
