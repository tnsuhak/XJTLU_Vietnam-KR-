from pathlib import Path
import re

p = Path('index.html')
text = p.read_text(encoding='utf-8')

text, count = re.subn(
    r'\n?\s*<!-- ===================== CTA BAND ===================== -->.*?(?=<style id="tns-mobile-news-lite-20260905">)',
    '\n',
    text,
    count=1,
    flags=re.DOTALL,
)

if count == 0:
    print('Korean homepage CTA band already removed')
else:
    p.write_text(text, encoding='utf-8')
    print('Korean homepage CTA band removed')
