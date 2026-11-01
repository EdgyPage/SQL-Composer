import html, re, sys
src = open(sys.argv[1], encoding="utf-8").read()
start_id, end_id = sys.argv[2], sys.argv[3]
s = src.find('id="%s"' % start_id)
e = src.find('id="%s"' % end_id, s + 1) if end_id != "-" else len(src)
chunk = src[s:e]
chunk = re.sub(r"<script.*?</script>", "", chunk, flags=re.S)
chunk = re.sub(r"<style.*?</style>", "", chunk, flags=re.S)
chunk = re.sub(r"<pre[^>]*>", "\n```\n", chunk)
chunk = re.sub(r"</pre>", "\n```\n", chunk)
chunk = re.sub(r"<(h[1-6]|p|li|div|tr|br)[^>]*>", "\n", chunk)
chunk = re.sub(r"<[^>]+>", "", chunk)
chunk = html.unescape(chunk)
chunk = re.sub(r"\n\s*\n+", "\n\n", chunk)
print(chunk)
