"""Make a minimal notebook from code cells separated by lines of '#%%' (my own helper)."""
import json, sys
src, dst = sys.argv[1], sys.argv[2]
text = open(src, encoding="utf-8").read()
parts = [p.strip("\n") + "\n" for p in text.split("#%%\n") if p.strip()]
cells = [{"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": p.splitlines(keepends=True)} for p in parts]
nb = {"cells": cells, "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
open(dst, "w", encoding="utf-8").write(json.dumps(nb, indent=1))
print("wrote", dst, len(cells), "cells")
