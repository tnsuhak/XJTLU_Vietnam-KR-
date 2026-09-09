from __future__ import annotations

from pathlib import Path
from bs4 import BeautifulSoup, Comment
from urllib.parse import urlparse
import json, re

SOURCE = Path('/tmp/xjtlu-vietnam-source')
TARGET = Path('.')

SKIP_TAGS = {'script','style','svg','path','noscript','code','pre'}
VIET_RE = re.compile(r'[ăâđêôơưĂÂĐÊÔƠƯ]|[àáạảãằắặẳẵầấậẩẫèéẹẻẽềếệểễìíịỉĩòóọỏõồốộổỗờớợởỡùúụủũừứựửữỳýỵỷỹ]', re.I)
SUSPICIOUS = [
    '전생','장학비','도저','도천','토주','후천 시립','지아토ング','비엔나티움',
    '브로체어','브로서','브로소','초기 새','조기동물','대도시청소년병원','학교의 생방송',
    '빨리 물어봐','월드클라이딩','중국 학생만 선택하지','연구 결과가 올라갑니다','제 말은,',
    '99,000만원','99.000만원','99,000원','99.000원','전학생 네트워크','수석생 네트워크',
]

def html_pages(root: Path):
    return sorted([p.relative_to(root).as_posix() for p in root.glob('*.html')] +
                  [p.relative_to(root).as_posix() for p in (root/'news').glob('*.html')])

def soup_for(root: Path, rel: str):
    return BeautifulSoup((root/rel).read_text(encoding='utf-8'), 'html.parser')

def internal_hrefs(soup: BeautifulSoup):
    out=set()
    for a in soup.find_all('a', href=True):
        h=a['href'].strip()
        if not h or h.startswith(('#','mailto:','tel:','javascript:')):
            continue
        u=urlparse(h)
        if u.scheme in ('http','https'):
            if u.netloc.endswith('xjtlu-vietnam.netlify.app') or u.netloc.endswith('xjtlu-vietnam-kr.netlify.app'):
                h=u.path or '/'
                if u.fragment: h += '#'+u.fragment
            else:
                continue
        elif u.scheme or u.netloc:
            continue
        if h.startswith('./'): h=h[2:]
        out.add(h)
    return sorted(out)

def youtube_ids(soup: BeautifulSoup):
    ids=[]
    for tag in soup.find_all(['iframe','a']):
        src=tag.get('src') or tag.get('href') or ''
        m=re.search(r'(?:youtube\.com/(?:embed/|watch\?v=)|youtu\.be/)([A-Za-z0-9_-]{6,})',src)
        if m: ids.append(m.group(1))
    return sorted(set(ids))

def metrics(soup: BeautifulSoup):
    body=soup.body or soup
    return {
        'h1': len(body.find_all('h1')),
        'h2': len(body.find_all('h2')),
        'h3': len(body.find_all('h3')),
        'section': len(body.find_all('section')),
        'details': len(body.find_all('details')),
        'table': len(body.find_all('table')),
        'iframe': len(body.find_all('iframe')),
        'internal_links': len(internal_hrefs(soup)),
    }

def visible_nodes(soup: BeautifulSoup):
    rows=[]
    for node in soup.find_all(string=True):
        if isinstance(node, Comment) or not node.parent or node.parent.name in SKIP_TAGS:
            continue
        t=' '.join(str(node).split())
        if t: rows.append((node.parent.name,t))
    return rows

source_pages=html_pages(SOURCE)
target_pages=html_pages(TARGET)
missing=sorted(set(source_pages)-set(target_pages))
extra=sorted(set(target_pages)-set(source_pages))
matched=sorted(set(source_pages)&set(target_pages))

page_reports={}
structural_mismatches=[]
for rel in matched:
    s=soup_for(SOURCE,rel); k=soup_for(TARGET,rel)
    sh=internal_hrefs(s); kh=internal_hrefs(k)
    sm,km=metrics(s),metrics(k)
    missing_hrefs=sorted(set(sh)-set(kh)); extra_hrefs=sorted(set(kh)-set(sh))
    sy,ky=youtube_ids(s),youtube_ids(k)
    page_reports[rel]={
        'source_metrics': sm,
        'korean_metrics': km,
        'missing_internal_hrefs_in_korean': missing_hrefs,
        'extra_internal_hrefs_in_korean': extra_hrefs,
        'source_youtube_ids': sy,
        'korean_youtube_ids': ky,
    }
    if sm!=km or missing_hrefs or extra_hrefs or sy!=ky:
        structural_mismatches.append(rel)

translation_flags=[]
visible_lines=[]
for rel in target_pages:
    soup=soup_for(TARGET,rel)
    for i,(tag,t) in enumerate(visible_nodes(soup),1):
        visible_lines.append(f'{rel}\t{i}\t{tag}\t{t}')
        reasons=[]
        if VIET_RE.search(t): reasons.append('Vietnamese-diacritic text')
        if re.search(r'(?<!장)학금',t): reasons.append('suspicious:standalone 학금')
        for bad in SUSPICIOUS:
            if bad in t: reasons.append('suspicious:'+bad)
        if re.search(r'\b(?:và|của|cho|với|được|sinh viên|học phí|tuyển sinh|ngành học)\b',t,re.I):
            reasons.append('Vietnamese phrase')
        if t in {'.',',',';',':'}:
            reasons.append('standalone punctuation')
        if reasons:
            translation_flags.append({'page':rel,'node':i,'tag':tag,'text':t,'reasons':reasons})

source_visible=[]
for rel in source_pages:
    soup=soup_for(SOURCE,rel)
    for i,(tag,t) in enumerate(visible_nodes(soup),1):
        source_visible.append(f'{rel}\t{i}\t{tag}\t{t}')

report={
    'source_branch':'preview/home-hero-copy-20260908',
    'source_html_pages':len(source_pages),
    'korean_html_pages':len(target_pages),
    'missing_in_korean':missing,
    'extra_in_korean':extra,
    'matched_pages':len(matched),
    'structural_mismatch_count':len(structural_mismatches),
    'structural_mismatches':structural_mismatches,
    'page_reports':page_reports,
    'translation_flag_count':len(translation_flags),
    'translation_flags':translation_flags,
}
Path('preview-parity-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
Path('review-visible-text-current.txt').write_text('\n'.join(visible_lines)+'\n',encoding='utf-8')
Path('vietnam-visible-text-current.txt').write_text('\n'.join(source_visible)+'\n',encoding='utf-8')

print('source pages:',len(source_pages))
print('korean pages:',len(target_pages))
print('missing:',missing)
print('extra:',extra)
print('structural mismatches:',structural_mismatches)
print('translation flags:',len(translation_flags))