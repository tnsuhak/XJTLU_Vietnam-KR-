from pathlib import Path
import re

START='<!-- TNS_SUBPAGE_CONTACT_START -->'
END='<!-- TNS_SUBPAGE_CONTACT_END -->'
STYLE='''<style id="tns-subpage-contact-style">.tns-subpage-contact{margin:50px auto 0;width:min(1000px,calc(100% - 36px));background:#14213d;border-radius:18px;padding:18px}.tns-subpage-contact-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.tns-subpage-contact a{display:flex;align-items:center;justify-content:center;min-height:54px;padding:13px 16px;border-radius:12px;background:#fff;color:#14213d!important;text-decoration:none!important;font-weight:800!important;text-align:center}.tns-subpage-contact a.zalo{background:#0068ff;color:#fff!important}.tns-subpage-office{margin-top:13px;padding-top:12px;border-top:1px solid rgba(255,255,255,.18);display:grid;grid-template-columns:1fr 1fr;gap:8px 20px;color:#c7cfdf;font-size:11.5px;line-height:1.55}.tns-subpage-office div{min-width:0}.tns-subpage-office b{color:#fff;font-size:11.5px}.tns-subpage-office a{display:inline!important;min-height:0!important;padding:0!important;border-radius:0!important;background:none!important;color:#fff!important;font-weight:700!important;text-decoration:none!important}.tns-subpage-office a:hover{text-decoration:underline!important}@media(max-width:720px){.tns-subpage-contact-grid{grid-template-columns:1fr}.tns-subpage-contact{padding:12px}.tns-subpage-office{grid-template-columns:1fr;font-size:11px;gap:7px}}</style>'''
BLOCK='''<!-- TNS_SUBPAGE_CONTACT_START -->\n<section class="tns-subpage-contact" aria-label="상담 연결"><div class="tns-subpage-contact-grid"><a href="tel:+842838233266">호치민 전화상담</a><a href="tel:+842432321239">하노이 전화상담</a><a class="zalo" href="https://zalo.me/0336737617" target="_blank" rel="noopener">Zalo 상담</a></div><div class="tns-subpage-office"><div><b>SOS 호치민</b><br>Tầng 3, Bcons Tower II, 42/1 Ung Văn Khiêm, P. Thạnh Mỹ Tây, TP.HCM · <a href="tel:+842838233266">+84 28 3823 3266</a></div><div><b>SOS 하노이</b><br>Tầng 6, Tòa Veam Tây Hồ, Khu D1, P. Tây Hồ, Hà Nội · <a href="tel:+842432321239">+84 24 3232 1239</a></div></div></section>\n<!-- TNS_SUBPAGE_CONTACT_END -->'''

pages=sorted(Path('.').glob('*.html'))+sorted(Path('news').glob('*.html'))
for p in pages:
    if p==Path('index.html'):
        continue
    s=p.read_text(encoding='utf-8')
    s=re.sub(r'<!-- TNS_SUBPAGE_CONTACT_START -->.*?<!-- TNS_SUBPAGE_CONTACT_END -->','',s,flags=re.S)
    s=re.sub(r'<style id="tns-subpage-contact-style">.*?</style>','',s,flags=re.S)
    s=re.sub(r'<section class="cta"[^>]*>.*?zalo\.me/0336737617.*?</section>','',s,flags=re.S|re.I)
    s=re.sub(r'<section[^>]*id="contact"[^>]*>.*?zalo\.me/0336737617.*?</section>','',s,flags=re.S|re.I)
    s=s.replace('</head>',STYLE+'\n</head>',1)
    if '</main>' in s:
        s=s.replace('</main>',BLOCK+'\n</main>',1)
    else:
        s=s.replace('</body>',BLOCK+'\n</body>',1)
    p.write_text(s,encoding='utf-8')

assert START not in Path('index.html').read_text(encoding='utf-8')
for p in pages:
    if p==Path('index.html'):
        continue
    s=p.read_text(encoding='utf-8')
    assert s.count(START)==1 and s.count(END)==1,p
    assert 'tel:+842838233266' in s and 'tel:+842432321239' in s and 'zalo.me/0336737617' in s,p
    assert 'Bcons Tower II' in s and 'Tòa Veam Tây Hồ' in s,p
print('standardized',len(pages)-1,'subpages with office details')
