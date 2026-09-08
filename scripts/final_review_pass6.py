from pathlib import Path
import re

pages = sorted(Path('.').glob('*.html')) + sorted(Path('news').glob('*.html'))

# Remove unnatural spaces between bold text and Korean postpositions.
particles = r'(?:에서는|에서|으로|에게|부터|까지|보다|처럼|마다|조차|이|가|을|를|은|는|와|과|에|로|의|도|만|께)'
particle_space = re.compile(r'</(b|strong)>\s+(?=' + particles + r'(?=[\s,.!?<]))')

PAGE_REPL = {
    'xjtlu-ranking-2027.html': {
        "<p>XJTLU는 2006년 University of Liverpool과 Xi'an Jiaotong University가 공동 설립한 독립 대학입니다. <b>Xi'an Jiaotong-Liverpool University</b>University of Liverpool 또는 Xi'an Jiaotong University의 순위로 대체해서 볼 수 없습니다.</p>":
        "<p>XJTLU는 2006년 University of Liverpool과 Xi'an Jiaotong University가 공동 설립한 독립 대학입니다. 따라서 <b>Xi'an Jiaotong-Liverpool University</b>의 자체 순위를 봐야 하며, University of Liverpool 또는 Xi'an Jiaotong University의 순위로 대체해서 볼 수 없습니다.</p>",
    },
    'xjtlu-2plus2-liverpool.html': {
        '<p>리버풀대학교는 XJTLU 2+2 학생에게 국제학생 학비 할인 제도를 안내하고 있습니다. <strong>국제학생 학비 10% 할인</strong> 리버풀대학교에서 공부하는 기간에 적용됩니다.</p>':
        '<p>리버풀대학교는 XJTLU 2+2 학생에게 국제학생 학비 할인 제도를 안내하고 있습니다. <strong>국제학생 학비 10% 할인</strong>은 리버풀대학교에서 공부하는 기간에 적용됩니다.</p>',
        '<p>학생 중 <strong>코호트 상위 5%</strong> 안내된 성적 기준을 충족하는 우수학생은 30% Merit Scholarship 대상이 될 수 있습니다. 이 장학금은 10% Partnership Discount와 중복 적용되지 않습니다. 실제 적용기준은 해당 연도 리버풀대학교 안내를 확인해야 합니다.</p>':
        '<p>학생 중 <strong>코호트 상위 5%</strong>에 해당하면서 STEM은 평균 80% 이상, 비-STEM은 평균 70% 이상 기준을 충족하면 30% Merit Scholarship 대상이 될 수 있습니다. 이 장학금은 10% Partnership Discount와 중복 적용되지 않습니다. 실제 적용기준은 해당 연도 리버풀대학교 안내를 확인해야 합니다.</p>',
    },
    'xjtlu-dieu-kien-tuyen-sinh-vietnam-2027.html': {
        '또는 <strong>TOEFL iBT 62</strong>.</p>': '또는 <strong>TOEFL iBT 62</strong>입니다.</p>',
        '<strong>TOEFL iBT 62</strong> 1학년 입학 영어조건으로 함께 안내됩니다.': '<strong>TOEFL iBT 62</strong>가 1학년 입학 영어조건으로 함께 안내됩니다.',
        '<strong>자동으로 적용되는 단순 환산 공식은 없습니다.</strong>이수학기,': '<strong>자동으로 적용되는 단순 환산 공식은 없습니다.</strong> 이수학기,',
    },
    'xjtlu-hoc-phi-hoc-bong-2027.html': {
        '<strong>연간 99,000 RMB</strong> 입니다.': '<strong>연간 99,000 RMB</strong>입니다.',
        '</a>학비와 장학금 조건은 입학연도에 따라 변경될 수 있습니다.': '</a><br/>학비와 장학금 조건은 입학연도에 따라 변경될 수 있습니다.',
    },
}

changed=[]
for p in pages:
    key=p.as_posix()
    s=p.read_text(encoding='utf-8')
    old=s
    s=particle_space.sub(r'</\1>', s)
    for a,b in PAGE_REPL.get(key,{}).items():
        s=s.replace(a,b)
    if s != old:
        p.write_text(s,encoding='utf-8')
        changed.append(key)

print('pass6 changed', len(changed), 'files')
for f in changed:
    print('-', f)
