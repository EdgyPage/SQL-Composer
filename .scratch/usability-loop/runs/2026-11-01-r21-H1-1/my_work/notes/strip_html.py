import html, re, sys
from pathlib import Path
src = Path(sys.argv[1]).read_text(encoding="utf-8")
start, end = sys.argv[2], sys.argv[3]
a = src.index(start)
b = src.index(end, a + 1) if end != "-" else len(src)
chunk = src[a:b]
chunk = re.sub(r"<(pre|/pre)[^>]*>", "\n", chunk)
chunk = re.sub(r"<br\s*/?>", "\n", chunk)
chunk = re.sub(r"</(p|li|h[1-6]|div|tr|section)>", "\n", chunk)
chunk = re.sub(r"<[^>]+>", "", chunk)
text = html.unescape(chunk)
text = re.sub(r"\n\s*\n+", "\n\n", text)
print(text)
