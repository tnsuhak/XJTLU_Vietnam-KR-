from __future__ import annotations

import re
from pathlib import Path
from bs4 import BeautifulSoup, Comment, NavigableString

ROOT = Path('.')

# Site-wide terminology and obvious machine-translation cleanup.
REPLACEMENTS = [
    ('도주 시안 지아토ング-리버풀대학교', '중국 쑤저우의 시안교통리버풀대학교'),
    ('시안 지아토ング-리버풀대학교', '시안교통리버풀대학교'),
    ('시안 지아토ڭ-리버풀대학교', '시안교통리버풀대학교'),
    ('시안 지아토ング 리버풀대학교', '시안교통리버풀대학교'),
    ('시안 자오퉁-리버풀 대학교', '시안교통리버풀대학교'),
    ('시안 자오퉁 리버풀 대학교', '시안교통리버풀대학교'),
    ('서안교통리버풀대학교', '시안교통리버풀대학교'),
    ('리버풀 대학교', '리버풀대학교'),
    ('토주', '쑤저우'),
    ('도주', '쑤저우'),
    ('Tô Châu', '쑤저우'),
    ('주, 중국', '중국 쑤저우'),
    ('주 &amp; 상하이', '쑤저우 &amp; 상하이'),
    ('주 & 상하이', '쑤저우 & 상하이'),
    ('태상', '타이창'),
    ('Thái Thương', '타이창'),
    ('Taicang', '타이창'),
    ('학금', '학비'),
    ('장학 &amp;', '장학금 &amp;'),
    ('장학 &', '장학금 &'),
    ('장학,', '장학금,'),
    ('중국 2027 유학', '2027 중국 유학'),
    ('중국 2027 여행', '2027 중국 유학'),
    ('중국 여행', '중국 유학'),
    ('연구 결과가 올라갑니다.', '졸업 후 진학 결과'),
    ('생상 영상', '학생생활 영상'),
    ('생상', '학생생활'),
    ('후천 시립', '호치민시'),
    ('호치민 시', '호치민시'),
    ('TP.HCM', '호치민시'),
    ('하노이 / 호치민시', '하노이 / 호치민시'),
    ('영국 중부 국제대학', '영국·중국 합작 국제대학'),
    ('영국 국제 대학', '영국·중국 합작 국제대학'),
    ('영국 국제대학', '영국·중국 합작 국제대학'),
    ('영국 중부 기업 대학', '영국·중국 합작 국제대학'),
    ('영국 중부기업 대학', '영국·중국 합작 국제대학'),
    ('중국 최대의 영국 중부 기업 대학', '중국의 대표적인 영국·중국 합작대학교'),
    ('중국 최대 영국 중부 기업 대학', '중국의 대표적인 영국·중국 합작대학교'),
    ('본 페이지 →', '메인 페이지 →'),
    ('자세한 내용을 확인해 보세요', '자세히 보기 →'),
    ('뉴스에서', '뉴스 보기 →'),
    ('2027년 중요한 랜드마크', '2027 주요 일정'),
    ('학업, 직업 &amp; 프로그램 선택', '전공, 진로 &amp; 프로그램 선택'),
    ('학업, 직업 & 프로그램 선택', '전공, 진로 & 프로그램 선택'),
    ('졸업 후의 성과', '졸업 후 진학 결과'),
    ('베트남 학생들의 조건', '베트남 학생 입학 조건'),
    ('2027년 중국 유학 지침', '2027 중국 유학 가이드'),
    ('XJTLU에서 영어로 대학을 공부합니다', 'XJTLU에서 영어로 대학 공부하기'),
    ('베트남어로 선택된 주목할 만한 공식 뉴스', '주요 공식 뉴스를 선별해 한국어로 확인'),
    ('학위: UoL + XJTLU', '학위: UoL + XJTLU'),
    ('학생이 있는 나라', '학생 출신 국가'),
    ('교육 프로그램', '교육 프로그램'),
    ('학생들', '학생'),
    ('편리한 비행길', '편리한 항공편'),
    ('2+2의 경로', '2+2 경로'),
    ('4+0의 경로', '4+0 경로'),
    ('중국에서 4년간 공부했습니다.', '4년 전 과정을 중국에서 이수'),
    ('영국과 중국에서 인정받았습니다.', '영국과 중국에서 인정되는 학위'),
    ('100%는 영어로 가르칩니다.', '100% 영어로 수업'),
    ('국제 프로그램, 글로벌 강사', '국제 프로그램 · 글로벌 교수진'),
    ('50%까지의 장학금', '최대 50% 입학 장학금'),
    ('학업 성취도를 기준으로 연간 연장', '학업 성취도에 따라 매년 연장'),
    ('Zalo에서 무료 상담', 'Zalo 무료 상담'),
    ('SOS 국제', 'SOS International'),
    ('SOS 인터내셔널', 'SOS International'),
    ('TNS 월드와이드', 'TNS Worldwide'),
    ('무료 상담', '무료 상담'),
    ('영어가 기본입니다.', '영어가 기본 수업 언어입니다.'),
    ('영어를 공부하는 것이 장점이고 중국어는 추가적인 장점입니다.', '전공은 영어로 공부하고, 중국어는 추가 경쟁력으로 쌓을 수 있습니다.'),
    ('리버풀대학교의 학위 구조', '리버풀대학교 학위 구조'),
    ('진정한 국제사회', '국제적인 학생 커뮤니티'),
    ('중국어 &amp; 중국에 대한 이해', '중국어 &amp; 중국 시장에 대한 이해'),
    ('중국어 & 중국에 대한 이해', '중국어 & 중국 시장에 대한 이해'),
    ('영국으로 가는 길', '영국 2+2 진학 경로'),
    ('물 속의 상황', '국내 위상'),
    ('우수한 대학 팀', '명문대 그룹'),
    ('베킹', '베이징대학교'),
    ('Hoa', '칭화대학교'),
    ('Cambridge', 'Cambridge'),
    ('오크스포드', 'Oxford'),
    ('캠브리지', 'Cambridge'),
    ('베트남 XJTLU', 'XJTLU 베트남'),
    ('XJTLU Vietnam', 'XJTLU 베트남'),
]

EXACT_TEXT = {
    'XJTLU: 초에 있는 영국 국제 대학': 'XJTLU: 중국 쑤저우의 영국·중국 합작 국제대학',
    'XJTLU: 초에 있는 영국 국제대학': 'XJTLU: 중국 쑤저우의 영국·중국 합작 국제대학',
    '영어로 전공을 공부하고, XJTLU와 상하이 근처의 리버풀대학교에서 학위를 받았다.': '중국 쑤저우에서 전공을 영어로 공부하고, 졸업 요건 충족 시 XJTLU 학위와 리버풀대학교 학위를 함께 받을 수 있습니다.',
    '2006년 정오에서 설립된': '2006년 중국 장쑤성 쑤저우에 설립',
    '28,000명 이상의 학생, 100개 이상의 프로그램, 90개 이상의 국가들의 학생': '28,000명 이상의 학생, 100개 이상의 프로그램, 90개 이상의 국가에서 온 학생들이 공부합니다.',
    '주소는 도쿄 (SIP) 에 있으며, 상하이와 빠른 연결이 있습니다.': '메인 캠퍼스는 쑤저우(SIP)에 있으며 상하이와 빠르게 연결됩니다.',
    '중국어와 비즈니스 중국어를 추가적으로 학습할 수 있습니다.': '재학 중 중국어와 Business Chinese를 추가로 배울 수 있습니다.',
    '몇몇 분야는 리버풀대학교로 가는 2+2 경로를 가지고 있습니다.': '일부 전공은 리버풀대학교로 이동하는 2+2 경로를 선택할 수 있습니다.',
    '중국 2027 유학: 조건, 비용, 장학금 &amp; 비자': '2027 중국 유학: 입학 조건, 비용, 장학금 &amp; 비자',
    '중국 2027 유학: 조건, 비용, 장학금 & 비자': '2027 중국 유학: 입학 조건, 비용, 장학금 & 비자',
    '베트남 학생을 위한 중국 2027 여행: 조건, 비용, 장학금, X1/X2 비자, 영어 프로그램 및 XJTLU 제안': '베트남 학생을 위한 2027 중국 유학 가이드: 입학 조건, 비용, 장학금, X1/X2 비자, 영어 프로그램과 XJTLU 정보.',
    '베트남 학생들의 중국 유학 설명서, 조건과 비용에서 장학금, 비자 및 영어 대학 교육 선택까지': '베트남 학생을 위한 중국 유학 안내: 입학 조건과 비용, 장학금, 비자, 영어 대학 과정 선택까지 정리했습니다.',
    '주요 자료 · 2026': '주요 수치 · 2026',
    '설립 년': '설립연도',
    '교육 프로그램': '교육 프로그램',
    '2026년 2학년도 졸업': '2026년 복수학위 졸업생',
    '두 명문학교가 XJTLU를 공동 설립했습니다.': '두 명문대학이 XJTLU를 공동 설립했습니다.',
    '물 속의 상황': '국내 위상',
    '우수한 대학 팀': '명문대 그룹',
    '세계 순위': '세계 순위',
    '영국 최고의 연구대학': '영국의 대표적인 연구중심대학',
    '중국 최고의 연구대학': '중국의 대표적인 연구중심대학',
}

# Head/meta overrides for the most important review pages. This is a review copy, not SEO production.
PAGE_TITLES = {
    'index.html': '[한글 검수판] XJTLU 베트남 2027 | 학비·장학금·입학·영국 학위',
    'xjtlu-dieu-kien-tuyen-sinh-vietnam-2027.html': '[한글 검수판] XJTLU 2027 입학조건 | 베트남 학생',
    'xjtlu-hoc-phi-hoc-bong-2027.html': '[한글 검수판] XJTLU 2027 학비·장학금',
    'xjtlu-nganh-hoc-nghe-nghiep.html': '[한글 검수판] XJTLU 전공·진로 2027',
    'xjtlu-2plus2-liverpool.html': '[한글 검수판] XJTLU 2+2 · 리버풀대학교 학위',
    'xjtlu-ranking-2027.html': '[한글 검수판] XJTLU 순위 2027 | QS·THE·ARWU',
    'xjtlu-doi-song-sinh-vien-the-thao-cau-lac-bo.html': '[한글 검수판] XJTLU 학생생활 · 스포츠 · 동아리',
    'du-hoc-trung-quoc-bang-tieng-anh-xjtlu.html': '[한글 검수판] 중국에서 영어로 대학 공부하기 | XJTLU',
    'du-hoc-trung-quoc-2027.html': '[한글 검수판] 2027 중국 유학 | 조건·비용·장학금·비자',
    'university-of-liverpool-vietnam.html': '[한글 검수판] 리버풀대학교 × 베트남 | XJTLU 연계 맥락',
    'xjtlu-ket-qua-hoc-len-sau-tot-nghiep-2025.html': '[한글 검수판] XJTLU 졸업 후 진학 결과 2025',
}

PAGE_H1 = {
    'du-hoc-trung-quoc-2027.html': '2027 중국 유학: 입학 조건, 비용, 장학금과 비자',
    'xjtlu-dieu-kien-tuyen-sinh-vietnam-2027.html': 'XJTLU 2027 입학 조건',
    'xjtlu-hoc-phi-hoc-bong-2027.html': 'XJTLU 2027 학비와 장학금',
    'xjtlu-nganh-hoc-nghe-nghiep.html': 'XJTLU 2027 전공과 진로',
    'xjtlu-2plus2-liverpool.html': 'XJTLU 2+2와 리버풀대학교 학위',
    'xjtlu-ranking-2027.html': 'XJTLU 2027 순위: QS, THE, ARWU',
    'xjtlu-doi-song-sinh-vien-the-thao-cau-lac-bo.html': 'XJTLU 학생생활: 스포츠, 동아리와 캠퍼스 생활',
    'du-hoc-trung-quoc-bang-tieng-anh-xjtlu.html': '중국에서 영어로 대학 공부하기: XJTLU란?',
    'university-of-liverpool-vietnam.html': '리버풀대학교는 베트남과 어떻게 연결되고 있나?',
    'xjtlu-ket-qua-hoc-len-sau-tot-nghiep-2025.html': 'XJTLU 졸업 후 진학 결과 2025',
}


def clean_text(text: str) -> str:
    out = text
    stripped = out.strip()
    if stripped in EXACT_TEXT:
        core = EXACT_TEXT[stripped]
        return out[:len(out)-len(out.lstrip())] + core + out[len(out.rstrip()):]
    for old, new in REPLACEMENTS:
        out = out.replace(old, new)
    # Small spacing/punctuation cleanup caused by MT.
    out = re.sub(r'\s+([,.!?])', r'\1', out)
    out = re.sub(r'\s{2,}', ' ', out) if '\n' not in out else out
    return out


def polish_html(path: Path) -> None:
    html = path.read_text(encoding='utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    skip = {'script', 'style', 'code', 'pre'}
    for node in list(soup.find_all(string=True)):
        if isinstance(node, Comment) or not node.parent or node.parent.name in skip:
            continue
        updated = clean_text(str(node))
        if updated != str(node):
            node.replace_with(NavigableString(updated))

    for tag in soup.find_all(True):
        for attr in ('content', 'aria-label', 'alt', 'title', 'placeholder'):
            value = tag.get(attr)
            if isinstance(value, str):
                tag[attr] = clean_text(value)

    rel = path.relative_to(ROOT).as_posix()
    if rel in PAGE_TITLES and soup.title:
        soup.title.string = PAGE_TITLES[rel]
    if rel in PAGE_H1:
        h1 = soup.find('h1')
        if h1:
            # Preserve homepage's multi-span hero H1; subpages can be safely replaced.
            if rel != 'index.html':
                h1.clear()
                h1.append(PAGE_H1[rel])

    # Homepage gets a curated core hero/intro polish because it is the main human review surface.
    if rel == 'index.html':
        kicker = soup.select_one('.hero-kicker')
        if kicker:
            # Keep flag SVGs, replace trailing text node only.
            text_nodes = [n for n in kicker.contents if isinstance(n, NavigableString) and n.strip()]
            if text_nodes:
                text_nodes[-1].replace_with(NavigableString('\n        영국·중국 합작 국제대학 · 중국 쑤저우\n      '))
        h1 = soup.find('h1')
        if h1:
            spans = h1.find_all('span', recursive=False)
            if len(spans) >= 4:
                spans[0].string = "XJTLU 베트남 · Xi'an Jiaotong-Liverpool University"
                spans[1].string = '리버풀대학교 학위'
                spans[2].string = '100% 영어 수업'
                spans[3].string = '중국 쑤저우 · 상하이 인근'
        sub = soup.select_one('.hero p.sub')
        if sub:
            sub.clear()
            sub.append("Xi'an Jiaotong-Liverpool University(XJTLU)는 중국 쑤저우에 있는 영국·중국 합작 국제대학입니다. 학부 전공을 영어로 공부하고, 졸업 요건을 충족하면 XJTLU 학위와 ")
            b = soup.new_tag('b'); b.string = 'University of Liverpool'
            sub.append(b)
            sub.append(' 학위를 함께 받을 수 있습니다.')
        actions = soup.select('.hero-actions a')
        if len(actions) >= 2:
            actions[0].string = '베트남 학생 입학조건 보기 →'
            actions[1].string = 'XJTLU 알아보기'

    path.write_text(str(soup), encoding='utf-8')


def main() -> None:
    pages = sorted(ROOT.glob('*.html')) + sorted((ROOT / 'news').glob('*.html'))
    assert len(pages) == 24, len(pages)
    for p in pages:
        polish_html(p)
    print(f'Polished {len(pages)} Korean review pages')


if __name__ == '__main__':
    main()
