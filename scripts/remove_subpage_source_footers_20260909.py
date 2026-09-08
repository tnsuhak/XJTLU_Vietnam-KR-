from pathlib import Path
import re

# Remove the small '자료 출처' footer blocks from ordinary guide pages only.
# News articles are intentionally excluded so their original-source links remain.
pages = [p for p in Path('.').glob('*.html') if p.name != 'index.html']
removed_total = 0

patterns = [
    r'\n?\s*<(?:div|section|p)\b[^>]*class=["\'][^"\']*\bsources\b[^"\']*["\'][^>]*>.*?</(?:div|section|p)>\s*',
    r'\n?\s*<(?:div|section|p)\b[^>]*class=["\'][^"\']*\bsource-footer\b[^"\']*["\'][^>]*>.*?</(?:div|section|p)>\s*',
]

for page in pages:
    text = page.read_text(encoding='utf-8')
    original = text
    for pattern in patterns:
        text, count = re.subn(pattern, '\n', text, flags=re.I | re.S)
        removed_total += count
    if text != original:
        page.write_text(text, encoding='utf-8')
        print('removed source footer:', page)

leftovers = []
for page in pages:
    text = page.read_text(encoding='utf-8')
    if re.search(r'class=["\'][^"\']*\b(?:sources|source-footer)\b', text, flags=re.I):
        leftovers.append(str(page))
if leftovers:
    raise SystemExit(f'source footer still present: {leftovers}')

print('ordinary Korean guide pages checked:', len(pages), 'removed blocks:', removed_total)
