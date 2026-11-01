"""Print project.check() for the Project, from its own copy of the Toolbox."""
import sys

sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r20-W5-1\my_project")
from sqlglot_composer import project  # noqa: E402

print(project.check())
