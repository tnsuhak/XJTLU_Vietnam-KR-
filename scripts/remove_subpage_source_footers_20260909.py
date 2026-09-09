from pathlib import Path
import re

RANKING = 'xjtlu-ranking-2027.html'

guide_pages = [p for p in Path('.').glob('*.html') if p.name not in {'index.html', RANKING}]
removed_total = 0
patterns = [
    r'\n?\s*<(?:div|section|p)\b[^>]*class=["\'][^"\']*\b(?:sources|source|source-footer)\b[^"\']*["\'][^>]*>.*?</(?:div|section|p)>\s*',
]
for page in guide_pages:
    text = page.read_text(encoding='utf-8')
    original = text
    for pattern in patterns:
        text, count = re.subn(pattern, '\n', text, flags=re.I | re.S)
        removed_total += count
    if text != original:
        page.write_text(text, encoding='utf-8')

all_html = sorted(Path('.').glob('*.html')) + sorted(Path('news').glob('*.html'))
link_re = re.compile(
    r'<a\b[^>]*href=["\'](?:https?://[^"\']+)?/?xjtlu-ranking-2027\.html(?:#[^"\']*)?["\'][^>]*>.*?</a>',
    re.I | re.S,
)
for page in all_html:
    if page.name == RANKING:
        continue
    text = page.read_text(encoding='utf-8')
    text = link_re.sub('', text)
    page.write_text(text, encoding='utf-8')

ranking = Path(RANKING)
if ranking.exists():
    ranking.unlink()

assert not ranking.exists()
for page in sorted(Path('.').glob('*.html')) + sorted(Path('news').glob('*.html')):
    raw = page.read_text(encoding='utf-8')
    assert RANKING not in raw, page
for page in guide_pages:
    if page.exists():
        raw = page.read_text(encoding='utf-8')
        assert not re.search(r'class=["\'][^"\']*\b(?:sources|source|source-footer)\b', raw, re.I), page
print('Korean ranking guide removed; ordinary guide source footers removed:', removed_total)