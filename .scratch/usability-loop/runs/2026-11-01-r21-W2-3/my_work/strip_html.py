import re, html, sys
src = open(sys.argv[1], encoding="utf-8").read()
src = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", "", src)
src = re.sub(r"(?i)<br\s*/?>", "\n", src)
src = re.sub(r"(?i)</(p|h[1-6]|li|tr|div|pre|section)>", "\n", src)
src = re.sub(r"<[^>]+>", "", src)
sys.stdout.buffer.write(html.unescape(src).encode("utf-8"))
