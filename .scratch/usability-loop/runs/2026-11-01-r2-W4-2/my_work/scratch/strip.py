import html, re, sys
from pathlib import Path
src = Path(sys.argv[1]).read_text(encoding="utf-8")
start, end = sys.argv[2], sys.argv[3]
i = src.index(f'id="{start}"')
j = src.index(f'id="{end}"', i) if end != "-" else len(src)
chunk = src[i:j]
chunk = re.sub(r"<script.*?</script>", "", chunk, flags=re.S)
chunk = re.sub(r"<style.*?</style>", "", chunk, flags=re.S)
chunk = re.sub(r"<(pre|/pre)[^>]*>", "\n", chunk)
chunk = re.sub(r"<br\s*/?>", "\n", chunk)
chunk = re.sub(r"</(p|li|h\d|tr|div|section)>", "\n", chunk)
chunk = re.sub(r"<[^>]+>", "", chunk)
chunk = html.unescape(chunk)
chunk = re.sub(r"\n\s*\n+", "\n\n", chunk)
print(chunk)
