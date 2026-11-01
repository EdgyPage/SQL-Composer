import re, html, sys
from pathlib import Path
src = Path(sys.argv[1]).read_text(encoding="utf-8")
start_id, end_id = sys.argv[2], sys.argv[3]
i = src.index('id="%s"' % start_id)
j = src.index('id="%s"' % end_id, i + 1) if end_id != "-" else len(src)
chunk = src[i:j]
chunk = re.sub(r"<pre[^>]*>", "\n[[PRE]]\n", chunk)
chunk = re.sub(r"</pre>", "\n[[/PRE]]\n", chunk)
chunk = re.sub(r"<(br|/p|/li|/h[1-6]|/div|/tr)[^>]*>", "\n", chunk)
chunk = re.sub(r"<[^>]+>", "", chunk)
text = html.unescape(chunk)
text = re.sub(r"\n\s*\n+", "\n\n", text)
print(text)
