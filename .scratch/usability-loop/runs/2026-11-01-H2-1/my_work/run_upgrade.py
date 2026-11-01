# Runs project.upgrade() from the Project's admin/ folder, as a cell of check_project.ipynb would.
import os
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-H2-1\my_project")
os.chdir(ROOT / "admin")
sys.path.insert(0, str(ROOT))

from sqlglot_composer import project  # noqa: E402

print(project.upgrade())
