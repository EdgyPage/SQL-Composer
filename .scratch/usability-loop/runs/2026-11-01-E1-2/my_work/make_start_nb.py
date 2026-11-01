import json, sys
from pathlib import Path
src = sys.argv[1]
nb = {
 "cells": [{"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": src.split("\n")}],
 "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
 "nbformat": 4, "nbformat_minor": 5,
}
for c in nb["cells"]:
    c["source"] = [l + "\n" for l in c["source"][:-1]] + [c["source"][-1]]
Path("start.ipynb").write_text(json.dumps(nb, indent=1), encoding="utf-8")
