import html, re, sys
text = open(sys.argv[1], encoding="utf-8").read()
text = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", "", text)
text = re.sub(r"(?i)<(br|/p|/li|/h\d|/section|/pre|/tr|/div)[^>]*>", "\n", text)
text = re.sub(r"<[^>]+>", "", text)
text = html.unescape(text)
text = re.sub(r"\n\s*\n+", "\n\n", text)
with open(sys.argv[2], "w", encoding="utf-8") as f:
    f.write(text)
