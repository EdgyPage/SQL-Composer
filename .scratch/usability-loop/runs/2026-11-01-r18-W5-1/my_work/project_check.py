"""Print project.check() for the Project, from its own folder."""
import sys
from pathlib import Path

project_root = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-W5-1\my_project")
sys.path.insert(0, str(project_root))
import os  # noqa: E402

os.chdir(project_root / "admin")
from sqlglot_composer import project  # noqa: E402

print(project.check())
