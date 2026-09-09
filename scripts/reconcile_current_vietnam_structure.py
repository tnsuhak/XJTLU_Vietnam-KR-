from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import sys

SOURCE=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('/tmp/xjtlu-vietnam-source')
ROOT=Path('.')
GUIDES={
 '/xjtlu-chi-phi-sinh-hoat-2027.html',
 '/xjtlu-ky-tuc-xa-sip-taicang.html',
 '/xjtlu-to-chau-thuong-hai-viet-nam.html',
}

def normalized_internal(soup):
    out=set()
    for a in soup.find_all('a',href=True):
        h=a['href'].strip()
        u=urlparse(h)
        if u.scheme in ('http','https'):
            if u.netloc.endswith('xjtlu-vietnam.netlify.app') or u.netloc.endswith('xjtlu-vietnam-kr.netlify.app'):
                h=u.path or '/'
            else:
                continue
        if h.startswith('./'): h='/'+h[2:]
        if h and not h.startswith(('#','mailto:','tel:','javascript:')) and not h.startswith('/'):
            h='/'+h
        out.add(h)
    return out

src_pages=sorted([p.relative_to(SOURCE).as_posix() for p in SOURCE.glob('*.html')]+[p.relative_to(SOURCE).as_posix() for p in (SOURCE/'news').glob('*.html')])
for rel in src_pages:
    kp=ROOT/rel
    if not kp.exists(): continue
    ss=BeautifulSoup((SOURCE/rel).read_text(encoding='utf-8'),'html.parser')
    ks=BeautifulSoup(kp.read_text(encoding='utf-8'),'html.parser')
    allowed=normalized_internal(ss)
    changed=False
    for href in GUIDES:
        if href not in allowed:
            for a in list(ks.find_all('a',href=href)):
                a.decompose(); changed=True
    if changed:
        kp.write_text(str(ks),encoding='utf-8')
print('reconciled current Vietnam guide-link parity')
