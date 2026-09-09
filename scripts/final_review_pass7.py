from pathlib import Path
from bs4 import BeautifulSoup, NavigableString

# Final human-language polish after syncing the current Vietnamese preview.
# Keep page structure intact; only improve Korean wording / number notation.

NEW_PAGES = [
    Path('xjtlu-chi-phi-sinh-hoat-2027.html'),
    Path('xjtlu-ky-tuc-xa-sip-taicang.html'),
    Path('xjtlu-to-chau-thuong-hai-viet-nam.html'),
]

NUM_REPL = {
    '3.700 RMB':'3,700 RMB', '6.450 RMB':'6,450 RMB', '9.600 RMB':'9,600 RMB',
    '1.800 RMB':'1,800 RMB', '2.700 RMB':'2,700 RMB', '3.500 RMB':'3,500 RMB',
    '1.300':'1,300', '1.800':'1,800', '3.000':'3,000', '1.000':'1,000', '2.000':'2,000',
    '6.000 RMB':'6,000 RMB', '14.000 RMB':'14,000 RMB',
    '6.000 RMB/':'6,000 RMB/', '14.000 RMB/':'14,000 RMB/',
    '204,75 tỷ RMB':'2,047.5억 RMB', '204.75 billion RMB':'2,047.5억 RMB',
    '25–30 phút':'25–30분', '5–15 phút':'5–15분',
    'Tô Châu & Thượng Hải':'쑤저우 & 상하이',
}
for p in NEW_PAGES:
    if not p.exists():
        continue
    s=p.read_text(encoding='utf-8')
    for a,b in NUM_REPL.items():
        s=s.replace(a,b)
    p.write_text(s,encoding='utf-8')

# Repair two Korean sentences whose linked anchor split the original Vietnamese
# sentence and left unnatural Korean fragments.
p=Path('du-hoc-trung-quoc-2027.html')
if p.exists():
    soup=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
    for para in soup.find_all('p'):
        text=para.get_text(' ',strip=True)
        link=para.find('a')
        if link and '베트남 학생 세부조건은' in text and 'XJTLU 2027 입학조건' in link.get_text(' ',strip=True):
            saved=link.extract()
            para.clear()
            para.append(NavigableString('베트남 학생의 상세 입학조건은 '))
            para.append(saved)
            para.append(NavigableString('에서 확인할 수 있습니다.'))
        elif link and text.startswith('XJTLU의 경우') and '학비' in link.get_text(' ',strip=True) and '장학금' in link.get_text(' ',strip=True):
            saved=link.extract()
            para.clear()
            para.append(NavigableString('XJTLU의 실제 학비·숙소·장학금은 '))
            para.append(saved)
            para.append(NavigableString('에서 확인하세요.'))
    p.write_text(str(soup),encoding='utf-8')

print('final Korean review pass7 applied')