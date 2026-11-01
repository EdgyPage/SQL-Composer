import json, sys
from pathlib import Path
out = Path(sys.argv[1])
cells = []
for src in sys.argv[2:]:
    cells.append({"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": src.splitlines(keepends=True)})
nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}}, "nbformat": 4, "nbformat_minor": 5}
out.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print("wrote", out)
