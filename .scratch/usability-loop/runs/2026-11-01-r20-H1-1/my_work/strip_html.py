import re, html, sys
src = open(sys.argv[1], encoding="utf-8").read()
text = re.sub(r"<script.*?</script>|<style.*?</style>", "", src, flags=re.S)
text = re.sub(r"<[^>]+>", "", text)
text = html.unescape(text)
text = re.sub(r"\n\s*\n+", "\n\n", text)
open(sys.argv[2], "w", encoding="utf-8").write(text)
print(len(text))
