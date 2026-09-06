from pathlib import Path
import re

PAGE = Path('xjtlu-doi-song-sinh-vien-the-thao-cau-lac-bo.html')
text = PAGE.read_text(encoding='utf-8')

text = text.replace(
    '.video-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}',
    '.video-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}',
)

new_section = '''<section class="section" id="video"><h2>영상으로 보는 XJTLU 스포츠 시설</h2><p class="lead">한국어 영상 대신 영어 영상 2개로 정리했습니다. SIP와 Taicang의 스포츠 시설을 각각 직접 확인할 수 있습니다.</p><div class="video-grid"><article class="video-card"><div class="video-frame"><iframe src="https://www.youtube-nocookie.com/embed/drOy9rzNmlE" title="XJTLU SIP 스포츠 시설" loading="lazy" allowfullscreen></iframe></div><div class="video-copy"><b>SIP · Suzhou 스포츠 시설</b><p>쑤저우 SIP 캠퍼스의 스포츠 공간과 시설을 영어 영상으로 확인합니다.</p><a href="https://www.youtube.com/watch?v=drOy9rzNmlE" target="_blank" rel="noopener">YouTube에서 열기 ↗</a></div></article><article class="video-card"><div class="video-frame"><iframe src="https://www.youtube-nocookie.com/embed/T8g0zoI9rO4" title="XJTLU Taicang 스포츠 시설" loading="lazy" allowfullscreen></iframe></div><div class="video-copy"><b>Taicang · XEC 스포츠 시설</b><p>타이창 캠퍼스의 스포츠 공간과 시설을 영어 영상으로 확인합니다.</p><a href="https://www.youtube.com/watch?v=T8g0zoI9rO4" target="_blank" rel="noopener">YouTube에서 열기 ↗</a></div></article></div></section>'''

pattern = re.compile(r'<section class="section" id="video">.*?</div></section>(?=<section class="section"><h2>쑤저우 생활)', re.S)
text, n = pattern.subn(new_section, text, count=1)
if n != 1:
    raise SystemExit('Video section not found')

for old_id in ('XciLskXWwIU', 'nVirGEvdcT8'):
    if old_id in text:
        raise SystemExit(f'Old video id still present: {old_id}')

for new_id in ('drOy9rzNmlE', 'T8g0zoI9rO4'):
    if new_id not in text:
        raise SystemExit(f'New video id missing: {new_id}')

PAGE.write_text(text, encoding='utf-8')
print('Replaced Korean-reference sports videos with English SIP and Taicang videos.')
