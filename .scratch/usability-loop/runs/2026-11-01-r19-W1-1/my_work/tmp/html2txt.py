import html, re, sys
src = open(sys.argv[1], encoding="utf-8").read()
src = re.sub(r"(?is)<(script|style).*?</\1>", "", src)
src = re.sub(r"(?i)<br\s*/?>", "\n", src)
src = re.sub(r"(?i)</(p|li|h[1-6]|div|tr|pre|section|table|ul|ol)>", "\n", src)
src = re.sub(r"<[^>]+>", "", src)
sys.stdout.buffer.write(html.unescape(src).encode("utf-8"))
