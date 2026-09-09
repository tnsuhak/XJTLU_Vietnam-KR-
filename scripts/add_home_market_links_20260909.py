from pathlib import Path

p = Path('index.html')
text = p.read_text(encoding='utf-8')

START = '<!-- VIETNAM-MARKET-HOME-LINKS-20260909 -->'
END = '<!-- /VIETNAM-MARKET-HOME-LINKS-20260909 -->'

# Remove an older copy first so the script stays idempotent.
if START in text and END in text:
    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    text = before.rstrip() + '\n' + after.lstrip()

anchor = '<div class="home-lite-actions"><a href="/xjtlu-doi-song-sinh-vien-the-thao-cau-lac-bo.html">XJTLU 학생생활 자세히 보기 →</a></div>'
if anchor not in text:
    raise RuntimeError('student-life homepage action anchor not found')

block = '''<!-- VIETNAM-MARKET-HOME-LINKS-20260909 -->
<div style="display:flex;flex-wrap:wrap;gap:8px 16px;margin-top:12px;font-size:12.5px;font-weight:700;color:#596273">
  <a href="/xjtlu-to-chau-thuong-hai-viet-nam.html">쑤저우·상하이 &amp; 베트남 →</a>
  <a href="/xjtlu-chi-phi-sinh-hoat-2027.html">XJTLU 생활비 2027 →</a>
  <a href="/xjtlu-ky-tuc-xa-sip-taicang.html">SIP &amp; 타이창 숙소 →</a>
</div>
<!-- /VIETNAM-MARKET-HOME-LINKS-20260909 -->'''

text = text.replace(anchor, anchor + '\n' + block, 1)

for href in (
    '/xjtlu-to-chau-thuong-hai-viet-nam.html',
    '/xjtlu-chi-phi-sinh-hoat-2027.html',
    '/xjtlu-ky-tuc-xa-sip-taicang.html',
):
    if href not in text:
        raise RuntimeError(f'missing homepage link: {href}')

p.write_text(text, encoding='utf-8')
print('Korean homepage market links normalized')
