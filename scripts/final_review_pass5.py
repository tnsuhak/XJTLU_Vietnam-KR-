from pathlib import Path
import re

ROOTS = [Path('.'), Path('news')]

# Korean review copy: final normalization for numbers, punctuation, and a few
# sentences that still read like literal translation after pass 4.
GLOBAL_REPL = {
    '99.000 RMB': '99,000 RMB',
    '7,0/10': '7.0/10',
    '86,43%': '86.43%',
    '47,16%': '47.16%',
    '93,40%': '93.40%',
    '>1.018<': '>1,018<',
    '>1.500+<': '>1,500+<',
    '>4.816<': '>4,816<',
    '>3.797<': '>3,797<',
    '>1.244<': '>1,244<',
    '<p>.</p>': '',
    '<p>,</p>': '',
}

PAGE_REPL = {
    'index.html': {
        '조건들을 보세요': '입학조건 확인 →',
        '시안교통리버풀대학교의 베트남어 정보 페이지는 TNS Worldwide (서울) 와 베트남의 컨설팅 파트너 SOS International (TP. 호치민 & 하노이) 에 의해 공동으로 작성되었습니다.':
        '시안교통리버풀대학교(XJTLU) 베트남어 정보 페이지는 TNS Worldwide(서울)와 베트남 현지 상담 파트너 SOS International(호치민·하노이)이 함께 운영합니다.',
    },
    'xjtlu-dieu-kien-tuyen-sinh-vietnam-2027.html': {
        'GPA 3.0/4.0 + SAT 1280 또는 ACT 27 + 2 AP: 4.4':
        'GPA 3.0/4.0 + SAT 1280 또는 ACT 27 + 2 AP: 4, 4',
    },
    'xjtlu-doi-song-sinh-vien-the-thao-cau-lac-bo.html': {
        '조정, 킥복싱, 양궁, 골프, 농구, 도지볼, 미식축구, 축구 등 다양한 종목을 즐길 수 있습니다.':
        '조정, 킥복싱, 양궁, 골프, 농구, 피구(도지볼), 미식축구, 축구 등 다양한 종목을 즐길 수 있습니다.',
    },
    'news/xjtlu-alumni-australia-2026.html': {
        '<p>2026년 8월 6일, <b>100명 이상의 XJTLU 졸업생</b> 이 시드니 하버에서 열린 20주년 기념 행사에 참석했습니다.':
        '<p>2026년 8월 6일, <b>100명 이상의 XJTLU 졸업생</b>이 시드니 하버에서 열린 20주년 기념 행사에 참석했습니다.',
        '<p>XJTLU는 호주가 졸업 후 대학원 진학과 커리어를 이어가는 주요 목적지 중 하나라고 소개했습니다. <b>2025년에는 XJTLU 학생 600명 이상이</b> 호주 주요 대학으로 진학했으며 대표적으로 <b>UNSW, 멜버른 대학교, 시드니 대학교</b>.</p>':
        '<p>XJTLU는 호주가 졸업 후 대학원 진학과 커리어를 이어가는 주요 목적지 중 하나라고 소개했습니다. <b>2025년에는 XJTLU 학생 600명 이상이</b> 호주 주요 대학으로 진학했으며, 대표적으로 <b>UNSW, 멜버른 대학교, 시드니 대학교</b>가 포함됩니다.</p>',
        '<p>XJTLU에 따르면 호주에서 졸업생들은 금융, 기술, 컨설팅, 의료, 건축 및 공공 연구 분야에서 일하고 있습니다. <b>시드니, 멜버른, 브리즈번</b>등에서 동문이 활동하고 있으며, <b>학교 자료에서는 졸업생의 61%가 중간관리자급 이상 직책에서 일하고 있다고 소개합니다.</b>.</p>':
        '<p>XJTLU에 따르면 호주 졸업생들은 금융, 기술, 컨설팅, 의료, 건축, 공공 연구 등 다양한 분야에서 일하고 있습니다. <b>시드니, 멜버른, 브리즈번</b> 등에서 동문이 활동하고 있으며, 학교 자료에서는 <b>졸업생의 61%가 중간관리자급 이상 직책에서 일하고 있다고 소개합니다.</b></p>',
        '<h2>호주 대학과의 연결도 계속되고 있습니다.</h2>': '<h2>호주 대학과의 연결도 계속되고 있습니다</h2>',
    },
    'news/xjtlu-alumni-singapore-2026.html': {
        '<p>XJTLU에 따르면 현재 <b>500명 이상의 XJTLU 졸업생이 싱가포르와 연결되어 있으며</b> 학업 또는 커리어를 위해 <b>약 150명의 졸업생이 현재 싱가포르에서 공부하거나 일하고 있습니다.</b>, 컴퓨터과학, 전자공학, 비즈니스 등 다양한 전공 배경을 갖고 있습니다.</p>':
        '<p>XJTLU에 따르면 <b>500명 이상의 졸업생이 싱가포르와 연결되어 있으며</b>, 이 가운데 <b>약 150명이 현재 싱가포르에서 공부하거나 일하고 있습니다.</b> 이들은 컴퓨터과학, 전자공학, 비즈니스 등 다양한 전공 배경을 갖고 있습니다.</p>',
        '<p>XJTLU가 소개한 싱가포르 진학 학생 수는 <b>3년 사이 57명에서 146명으로 증가</b>이것은 주목할만한 지표입니다. 싱가포르는 아시아의 최고의 교육 중심지이자 동남아 학생의 국제적인 일자리 시장 중 하나입니다.</p>':
        '<p>XJTLU가 소개한 싱가포르 진학 학생 수는 <b>3년 사이 57명에서 146명으로 증가</b>했습니다. 이는 주목할 만한 지표입니다. 싱가포르는 아시아의 주요 교육 중심지이자 동남아 학생이 국제적인 커리어를 쌓는 대표 시장 중 하나입니다.</p>',
    },
    'news/xjtlu-harvard-full-scholarship-stanford-yale-oxford.html': {
        '<p>XJTLU에 따르면 Li는 <b>Stanford University, Yale University</b> 와 <b>University of Oxford</b>향후 계산생물학, 데이터, AI 도구를 결합하는 연구방향을 발전시키고자 한다고 소개했습니다.</p>':
        '<p>XJTLU에 따르면 Li는 <b>Stanford University, Yale University</b>와 <b>University of Oxford</b>에서도 offer를 받았습니다. 향후 계산생물학, 데이터, AI 도구를 결합하는 연구방향을 발전시키고자 한다고 소개했습니다.</p>',
    },
}

META = {
    'news/xjtlu-alumni-australia-2026.html': 'XJTLU는 2025년 600명 이상의 학생이 호주 주요 대학으로 진학했다고 소개했습니다. 시드니·멜버른·브리즈번의 졸업생 네트워크와 진학 사례를 정리합니다.',
    'news/xjtlu-alumni-singapore-2026.html': 'XJTLU가 공개한 싱가포르 동문·진학 네트워크를 정리합니다. 500명 이상의 졸업생 연결과 현재 약 150명의 현지 학업·근무 사례를 소개합니다.',
    'news/xjtlu-class-2026-liverpool-degrees.html': 'XJTLU 2026 졸업식에서 학부생 3,797명이 XJTLU와 University of Liverpool 학위를 받은 사례와 학위구조를 정리합니다.',
    'news/xjtlu-della-vivo-vietnam-southeast-asia.html': 'XJTLU BA Marketing 졸업생 Della Senjaya가 Vivo Indonesia에서 베트남을 포함한 동남아 시장 관련 업무를 하는 커리어 사례를 소개합니다.',
    'news/xjtlu-to-tsinghua-indonesian-student.html': 'XJTLU BA Marketing을 공부한 인도네시아 학생 Metta Hormen이 인턴십 경험을 쌓고 Tsinghua University 석사과정 offer를 받은 사례입니다.',
    'news/xjtlu-thai-graduate-cp-group.html': 'XJTLU BA Business Administration 졸업생 Pathikorn Luangpaiboonsri가 태국 CP Group에서 Management Trainee로 커리어를 시작한 사례입니다.',
    'news/xjtlu-harvard-cambridge-linguistics.html': 'XJTLU 졸업생 Yiran Du가 Harvard 교육 석사를 거쳐 Cambridge 교육 박사과정으로 이어간 학업 경로를 소개합니다.',
    'news/xjtlu-harvard-full-scholarship-stanford-yale-oxford.html': 'XJTLU Biomedical Statistics 졸업생 Jiayi Li가 Harvard 석사 전액 장학금과 Stanford·Yale·Oxford offer를 받은 사례를 정리합니다.',
    'news/xjtlu-to-upenn-behavioral-decision-sciences.html': 'XJTLU 졸업생 Yunzhou Zhong가 PwC 인턴십과 SURF 연구경험을 거쳐 University of Pennsylvania 대학원으로 진학한 사례입니다.',
    'news/xjtlu-to-oxford-english-literature.html': 'XJTLU English Studies 졸업생 Yuzhi Chen이 학부 연구경험을 바탕으로 University of Oxford에서 영문학 관련 학업을 이어간 사례입니다.',
    'news/xjtlu-filmmaking-to-columbia-university.html': 'XJTLU Filmmaking 졸업생 Yue Ren이 Columbia University와 미국 주요 영화대학에서 offer를 받은 진학 사례를 소개합니다.',
    'news/700-sinh-vien-indonesia-xjtlu-dong-nam-a.html': 'XJTLU의 인도네시아 학생 약 700명과 신규 지원 1,500건 이상 사례를 통해 동남아 학생 커뮤니티와 ASEAN 네트워크를 살펴봅니다.',
}

changed=[]
for root in ROOTS:
    for p in sorted(root.glob('*.html')):
        key=p.as_posix()
        s=p.read_text(encoding='utf-8')
        old=s
        for a,b in GLOBAL_REPL.items():
            s=s.replace(a,b)
        for a,b in PAGE_REPL.get(key,{}).items():
            s=s.replace(a,b)
        if key in META:
            desc=META[key]
            s, n = re.subn(r'<meta content="[^"]*" name="description"\s*/>', f'<meta content="{desc}" name="description"/>', s, count=1)
            if n != 1:
                raise RuntimeError(f'meta description not uniquely found: {key} ({n})')
        if s != old:
            p.write_text(s,encoding='utf-8')
            changed.append(key)

print('pass5 changed',len(changed),'files')
for f in changed:
    print('-',f)
