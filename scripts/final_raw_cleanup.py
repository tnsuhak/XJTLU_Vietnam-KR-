from pathlib import Path

REPL = {
    # Do scholarship fixes before the generic 학금 -> 학비 correction.
    '장학비': '장학금',
    '학금': '학비',
    '토주': '쑤저우',
    '도주 시안': '중국 쑤저우의 시안',
    '서안교통리버풀대학교': '시안교통리버풀대학교',
    '시안 자오퉁-리버풀 대학교': '시안교통리버풀대학교',
    '시안 지아토ング-리버풀대학교': '시안교통리버풀대학교',
    '시안 지아토ング 리버풀대학교': '시안교통리버풀대학교',
    '시안 지아토ング': '시안교통리버풀',
    '중국 2027 여행': '2027 중국 유학',
    '연구 결과가 올라갑니다.': '졸업 후 진학 결과',
    '주, 중국': '중국 쑤저우',
    '>주<': '>쑤저우<',
    '도쿄 (SIP)': '쑤저우(SIP)',
    '정오에서': '쑤저우에서',
    '후천 시립': '호치민시',
    '생상 영상': '학생생활 영상',
    '중국에서 4년간 공부했습니다.': '4년 전 과정을 중국에서 이수',
    '50%까지의 장학금': '최대 50% 입학 장학금',
    '100%는 영어로 가르칩니다.': '100% 영어로 수업',
}

pages = sorted(Path('.').glob('*.html')) + sorted(Path('news').glob('*.html'))
assert len(pages) == 24, len(pages)
for p in pages:
    text = p.read_text(encoding='utf-8')
    for old, new in REPL.items():
        text = text.replace(old, new)
    # The generic 학금 rule can turn 장학금 into 장학비; normalize once more at the end.
    text = text.replace('장학비', '장학금')
    p.write_text(text, encoding='utf-8')
print('Raw-cleaned', len(pages), 'pages')
