from pathlib import Path
import re

RANK_HREF = '/xjtlu-ranking-2027.html'
PAGES = sorted(Path('.').glob('*.html')) + sorted(Path('news').glob('*.html'))

GRID = '''<div class="tns-site-menu-grid">
<section class="tns-site-menu-group"><h3><a href="/">XJTLU 소개 <small>메인 페이지 →</small></a></h3><a href="/xjtlu-2plus2-liverpool.html">리버풀대학교 학위 &amp; 2+2 경로</a><a href="/university-of-liverpool-vietnam.html">리버풀 &amp; 베트남</a><a href="/xjtlu-to-chau-thuong-hai-viet-nam.html">쑤저우·상하이 &amp; 베트남</a></section>
<section class="tns-site-menu-group"><h3><a href="/xjtlu-nganh-hoc-nghe-nghiep.html">전공 &amp; 진로 <small>자세히 보기 →</small></a></h3><a href="/xjtlu-nganh-hoc-nghe-nghiep.html">전공, 진로 &amp; 프로그램 선택</a><a href="/xjtlu-ket-qua-hoc-len-sau-tot-nghiep-2025.html">졸업 후 진학 결과</a></section>
<section class="tns-site-menu-group"><h3><a href="/xjtlu-hoc-phi-hoc-bong-2027.html">학비 &amp; 장학금 <small>2027 →</small></a></h3><a href="/xjtlu-hoc-phi-hoc-bong-2027.html">학비, 장학금 &amp; 2027 주요 일정</a><a href="/xjtlu-chi-phi-sinh-hoat-2027.html">XJTLU 생활비 2027</a></section>
<section class="tns-site-menu-group"><h3><a href="/xjtlu-doi-song-sinh-vien-the-thao-cau-lac-bo.html">학생 생활 <small>자세히 보기 →</small></a></h3><a href="/xjtlu-doi-song-sinh-vien-the-thao-cau-lac-bo.html#the-thao">스포츠 &amp; 스포츠 시설</a><a href="/xjtlu-doi-song-sinh-vien-the-thao-cau-lac-bo.html#cau-lac-bo">클럽 &amp; 학생 조직</a><a href="/xjtlu-doi-song-sinh-vien-the-thao-cau-lac-bo.html#video">XJTLU 학생생활 영상</a><a href="/xjtlu-ky-tuc-xa-sip-taicang.html">SIP &amp; 타이창 숙소</a></section>
<section class="tns-site-menu-group"><h3><a href="/xjtlu-dieu-kien-tuyen-sinh-vietnam-2027.html">2027 입학 <small>자세히 보기 →</small></a></h3><a href="/xjtlu-dieu-kien-tuyen-sinh-vietnam-2027.html">베트남 학생 입학 조건</a></section>
<section class="tns-site-menu-group"><h3><a href="/du-hoc-trung-quoc-2027.html">중국 유학 <small>2027 →</small></a></h3><a href="/du-hoc-trung-quoc-2027.html">2027 중국 유학 가이드</a><a href="/du-hoc-trung-quoc-bang-tieng-anh-xjtlu.html">XJTLU에서 영어로 대학 공부하기</a></section>
<section class="tns-site-menu-group"><h3><a href="/news/">XJTLU 뉴스 <small>뉴스 보기 →</small></a></h3><a href="/news/">주요 공식 뉴스를 선별해 한국어로 확인 →</a></section>
</div>'''

GRID_RE = re.compile(r'<div class=["\']tns-site-menu-grid["\']>.*?</div>', re.I | re.S)
EXPECTED = {
    '/xjtlu-to-chau-thuong-hai-viet-nam.html',
    '/xjtlu-chi-phi-sinh-hoat-2027.html',
    '/xjtlu-ky-tuc-xa-sip-taicang.html',
}

changed=[]
for p in PAGES:
    text=p.read_text(encoding='utf-8')
    matches=list(GRID_RE.finditer(text))
    if not matches:
        raise RuntimeError(f'{p}: grouped menu grid not found')
    new_text=GRID_RE.sub(GRID,text)
    for href in EXPECTED:
        if href not in new_text:
            raise RuntimeError(f'{p}: missing {href}')
    if RANK_HREF in GRID:
        raise RuntimeError('ranking link unexpectedly present in canonical grid')
    if new_text!=text:
        p.write_text(new_text,encoding='utf-8')
        changed.append(str(p))

print('Canonical Korean grouped menu applied:',len(changed),'pages changed')
