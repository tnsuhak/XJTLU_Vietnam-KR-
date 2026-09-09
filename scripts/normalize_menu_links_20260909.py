from pathlib import Path
import re

CITY_HREF = '/xjtlu-to-chau-thuong-hai-viet-nam.html'
COST_HREF = '/xjtlu-chi-phi-sinh-hoat-2027.html'
DORM_HREF = '/xjtlu-ky-tuc-xa-sip-taicang.html'
RANK_HREF = '/xjtlu-ranking-2027.html'

PAGES = sorted(Path('.').glob('*.html')) + sorted(Path('news').glob('*.html'))


def split_menu(text: str):
    if '<!-- TNS_GLOBAL_MENU_START -->' in text and '<!-- TNS_GLOBAL_MENU_END -->' in text:
        a, rest = text.split('<!-- TNS_GLOBAL_MENU_START -->', 1)
        menu, b = rest.split('<!-- TNS_GLOBAL_MENU_END -->', 1)
        return a + '<!-- TNS_GLOBAL_MENU_START -->', menu, '<!-- TNS_GLOBAL_MENU_END -->' + b

    marker = 'id="siteMenu"'
    pos = text.find(marker)
    if pos < 0:
        return None
    start = text.rfind('<div', 0, pos)
    if start < 0:
        return None
    end = text.find('<header class="hero"', pos)
    if end < 0:
        end = text.find('<header class="hero ', pos)
    if end < 0:
        return None
    return text[:start], text[start:end], text[end:]


def add_after_first_available_href(menu: str, hrefs, new_anchor: str):
    for href in hrefs:
        pat = re.compile(r'(<a\b[^>]*href=["\']' + re.escape(href) + r'["\'][^>]*>.*?</a>)', re.I | re.S)
        m = pat.search(menu)
        if m:
            return menu[:m.end()] + new_anchor + menu[m.end():]
    raise RuntimeError(f'no anchor found from: {hrefs}')


def add_after_last_href(menu: str, href: str, new_anchor: str):
    pat = re.compile(r'<a\b[^>]*href=["\']' + re.escape(href) + r'["\'][^>]*>.*?</a>', re.I | re.S)
    matches = list(pat.finditer(menu))
    if not matches:
        raise RuntimeError(f'anchor not found: {href}')
    m = matches[-1]
    return menu[:m.end()] + new_anchor + menu[m.end():]


def add_after_last_studentlife_href(menu: str, new_anchor: str):
    pat = re.compile(r'<a\b[^>]*href=["\']/xjtlu-doi-song-sinh-vien-the-thao-cau-lac-bo\.html(?:#[^"\']*)?["\'][^>]*>.*?</a>', re.I | re.S)
    matches = list(pat.finditer(menu))
    if not matches:
        raise RuntimeError('student-life anchor not found')
    m = matches[-1]
    return menu[:m.end()] + new_anchor + menu[m.end():]


def remove_cost_link_from_heading(menu: str) -> str:
    def clean_h3(match):
        block = match.group(0)
        return re.sub(
            r'<a\b[^>]*href=["\']' + re.escape(COST_HREF) + r'["\'][^>]*>.*?</a>',
            '',
            block,
            flags=re.I | re.S,
        )
    return re.sub(r'<h3\b[^>]*>.*?</h3>', clean_h3, menu, flags=re.I | re.S)


def cost_link_nested_in_heading(menu: str) -> bool:
    return any(COST_HREF in block for block in re.findall(r'<h3\b[^>]*>.*?</h3>', menu, flags=re.I | re.S))


changed = []
for p in PAGES:
    text = p.read_text(encoding='utf-8')
    parts = split_menu(text)
    if not parts:
        raise RuntimeError(f'{p}: site menu not found')
    before, menu, after = parts

    menu = re.sub(
        r'\s*<a\b[^>]*href=["\']' + re.escape(RANK_HREF) + r'["\'][^>]*>.*?</a>',
        '',
        menu,
        flags=re.I | re.S,
    )

    menu = remove_cost_link_from_heading(menu)

    if f'href="{CITY_HREF}"' not in menu and f"href='{CITY_HREF}'" not in menu:
        menu = add_after_first_available_href(
            menu,
            ['/university-of-liverpool-vietnam.html', '/xjtlu-2plus2-liverpool.html', '/'],
            f'<a href="{CITY_HREF}">쑤저우·상하이 &amp; 베트남</a>',
        )

    if f'href="{COST_HREF}"' not in menu and f"href='{COST_HREF}'" not in menu:
        menu = add_after_last_href(
            menu,
            '/xjtlu-hoc-phi-hoc-bong-2027.html',
            f'<a href="{COST_HREF}">XJTLU 생활비 2027</a>',
        )

    if f'href="{DORM_HREF}"' not in menu and f"href='{DORM_HREF}'" not in menu:
        menu = add_after_last_studentlife_href(
            menu,
            f'<a href="{DORM_HREF}">SIP &amp; 타이창 숙소</a>',
        )

    for href in (CITY_HREF, COST_HREF, DORM_HREF):
        if href not in menu:
            raise RuntimeError(f'{p}: missing menu href {href}')
    if RANK_HREF in menu:
        raise RuntimeError(f'{p}: stale ranking menu href')
    if cost_link_nested_in_heading(menu):
        raise RuntimeError(f'{p}: living-cost link nested inside heading')

    new_text = before + menu + after
    if new_text != text:
        p.write_text(new_text, encoding='utf-8')
        changed.append(str(p))

print('Normalized Korean grouped menus:', len(changed), 'pages changed')
for name in changed:
    print(' -', name)
