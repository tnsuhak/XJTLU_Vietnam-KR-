from __future__ import annotations

import json
import os
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup, Comment, NavigableString

SOURCE = Path(sys.argv[1]).resolve()
TARGET = Path(sys.argv[2]).resolve()
REVIEW_HOST = "https://xjtlu-vietnam-kr.netlify.app"
PROD_HOST = "https://xjtlu-vietnam.netlify.app"

SKIP_DIRS = {".git", ".github", "scripts", "__pycache__"}
COPY_FILE_SUFFIXES = {
    ".html", ".htm", ".json", ".png", ".jpg", ".jpeg", ".webp", ".svg", ".ico", ".gif", ".avif", ".webmanifest"
}

VI_DIACRITICS = re.compile(r"[ăâđêôơưĂÂĐÊÔƠƯàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵÀÁẢÃẠẰẮẲẴẶẦẤẨẪẬÈÉẺẼẸỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌỒỐỔỖỘỜỚỞỠỢÙÚỦŨỤỪỨỬỮỰỲÝỶỸỴ]")
LETTER_RE = re.compile(r"[A-Za-zÀ-ỹ가-힣]")
SHORT_PROPER = re.compile(r"^(XJTLU|QS|THE|ARWU|C9|AI|STEM|IELTS|TOEFL|VND|RMB|GBP|USD|TNS|SOS|Zalo|SIP|XEC|HCMC|TP\. ?HCM)$", re.I)
SEP = "__TNSSEP9F3A__"

MANUAL_EXACT = {
    "Menu": "메뉴",
    "XJTLU Việt Nam": "XJTLU 베트남",
    "Trang chính": "메인",
    "Xem chi tiết": "자세히 보기",
    "Xem tin": "뉴스 보기",
    "Xem tất cả tin": "전체 뉴스 보기",
    "Tin tức XJTLU": "XJTLU 뉴스",
    "Giới thiệu XJTLU": "XJTLU 소개",
    "Ngành học & nghề nghiệp": "전공 & 진로",
    "Học phí & học bổng": "학비 & 장학금",
    "Đời sống sinh viên": "학생 생활",
    "Tuyển sinh 2027": "2027 입학",
    "Du học Trung Quốc": "중국 유학",
    "Liên hệ": "상담 문의",
    "Hỏi đáp": "FAQ",
    "Video": "영상",
    "Nguồn": "출처",
    "Nguồn chính thức": "공식 출처",
    "Tài liệu nguồn": "자료 출처",
    "Đọc thêm": "더 보기",
    "Quay lại": "돌아가기",
    "Cập nhật": "업데이트",
}

POST_REPLACEMENTS = [
    ("서안교통리버풀대학교", "시안교통리버풀대학교"),
    ("시안 자오퉁-리버풀 대학교", "시안교통리버풀대학교"),
    ("시안 자오퉁 리버풀 대학교", "시안교통리버풀대학교"),
    ("리버풀 대학교", "리버풀대학교"),
    ("쑤저우 중국", "중국 쑤저우"),
    ("호치민 시", "호치민시"),
    ("SOS 인터내셔널", "SOS International"),
    ("TNS 월드와이드", "TNS Worldwide"),
]

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 TNS-Korean-Review-Sync/2.0"})
cache: dict[str, str] = dict(MANUAL_EXACT)
failures: list[dict[str, str]] = []


def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def should_translate(text: str) -> bool:
    t = normalize_ws(text)
    if not t or not LETTER_RE.search(t):
        return False
    if SHORT_PROPER.fullmatch(t):
        return False
    if re.fullmatch(r"https?://\S+", t):
        return False
    if t.startswith("data:"):
        return False
    if len(t) == 1:
        return False
    return True


def postprocess(text: str) -> str:
    for a, b in POST_REPLACEMENTS:
        text = text.replace(a, b)
    return text


def translate_remote(text: str, record_failure: bool = True) -> str | None:
    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": "ko",
        "dt": "t",
        "q": text,
    }
    last_error = None
    for attempt in range(4):
        try:
            r = session.get("https://translate.googleapis.com/translate_a/single", params=params, timeout=20)
            r.raise_for_status()
            data = r.json()
            out = "".join(part[0] for part in data[0] if part and part[0])
            return postprocess(out)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(0.5 * (attempt + 1))
    if record_failure:
        failures.append({"text": text[:300], "error": str(last_error)})
    return None


def prime_cache(strings: Iterable[str]) -> None:
    unique: list[str] = []
    seen = set(cache)
    for raw in strings:
        t = normalize_ws(raw)
        if not should_translate(t) or t in seen:
            continue
        seen.add(t)
        unique.append(t)

    print(f"Priming translation cache for {len(unique)} unique strings", flush=True)
    batches: list[list[str]] = []
    current: list[str] = []
    current_len = 0
    for text in unique:
        # Google unofficial endpoint is safest below ~4k characters per request.
        extra = len(text) + len(SEP) + 4
        if current and (len(current) >= 16 or current_len + extra > 3300):
            batches.append(current)
            current = []
            current_len = 0
        current.append(text)
        current_len += extra
    if current:
        batches.append(current)

    for idx, batch in enumerate(batches, 1):
        payload = (f"\n{SEP}\n").join(batch)
        translated = translate_remote(payload, record_failure=False)
        parts = []
        if translated is not None:
            parts = re.split(rf"\s*{re.escape(SEP)}\s*", translated)
        if len(parts) == len(batch):
            for source, target in zip(batch, parts):
                cache[source] = postprocess(target.strip())
        else:
            # Fallback only for the unusual batch where the separator was altered.
            for source in batch:
                one = translate_remote(source, record_failure=True)
                cache[source] = postprocess(one.strip()) if one is not None else source
        if idx % 10 == 0 or idx == len(batches):
            print(f"  translated batch {idx}/{len(batches)}", flush=True)
        time.sleep(0.03)


def google_translate(text: str) -> str:
    raw = text
    t = normalize_ws(raw)
    if not should_translate(t):
        return raw

    leading = raw[: len(raw) - len(raw.lstrip())]
    trailing = raw[len(raw.rstrip()) :]
    translated = cache.get(t)
    if translated is None:
        translated = translate_remote(t, record_failure=True) or t
        cache[t] = translated
    return leading + postprocess(translated) + trailing


def copy_source_site() -> None:
    for item in TARGET.iterdir():
        if item.name in {".git", ".github", "scripts"}:
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

    for src in SOURCE.iterdir():
        if src.name in SKIP_DIRS:
            continue
        if src.is_dir():
            if src.name == "news" or src.name in {"assets", "images", "img", "static"}:
                shutil.copytree(src, TARGET / src.name)
            continue
        if src.suffix.lower() in COPY_FILE_SUFFIXES:
            shutil.copy2(src, TARGET / src.name)

    (TARGET / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    sitemap = TARGET / "sitemap.xml"
    if sitemap.exists():
        sitemap.unlink()


def strip_indexing_metadata(soup: BeautifulSoup) -> None:
    for tag in soup.find_all("meta", attrs={"name": re.compile(r"^robots$", re.I)}):
        tag.decompose()
    robots = soup.new_tag("meta")
    robots["name"] = "robots"
    robots["content"] = "noindex, nofollow, noarchive, nosnippet"
    if soup.head:
        soup.head.insert(0, robots)

    for tag in soup.find_all("link", attrs={"rel": lambda x: x and "canonical" in x}):
        tag.decompose()
    for tag in soup.find_all("meta", attrs={"property": "og:url"}):
        tag.decompose()
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        tag.decompose()


def collect_html_strings(path: Path) -> list[str]:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    out: list[str] = []
    if soup.title and soup.title.string:
        out.append(str(soup.title.string))
    for meta_key in ("description", "twitter:title", "twitter:description"):
        tag = soup.find("meta", attrs={"name": meta_key})
        if tag and tag.get("content"):
            out.append(tag["content"])
    for prop in ("og:title", "og:description", "og:site_name"):
        tag = soup.find("meta", attrs={"property": prop})
        if tag and tag.get("content"):
            out.append(tag["content"])
    skip_parents = {"script", "style", "svg", "path", "noscript", "code", "pre"}
    for node in soup.find_all(string=True):
        if isinstance(node, Comment) or not node.parent or node.parent.name in skip_parents:
            continue
        if should_translate(str(node)):
            out.append(str(node))
    for tag in soup.find_all(True):
        for attr in ("alt", "title", "aria-label", "placeholder"):
            value = tag.get(attr)
            if isinstance(value, str) and should_translate(value):
                out.append(value)
    return out


def collect_json_strings(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    out: list[str] = []

    def walk(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
        elif isinstance(obj, str) and not obj.startswith(("http://", "https://")) and should_translate(obj):
            out.append(obj)

    walk(data)
    return out


def translate_html(path: Path) -> None:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    if soup.html:
        soup.html["lang"] = "ko"
    strip_indexing_metadata(soup)

    if soup.title and soup.title.string:
        title = google_translate(str(soup.title.string)).strip()
        if not title.startswith("[한글 검수판]"):
            title = "[한글 검수판] " + title
        soup.title.string.replace_with(title)

    for meta_key in ("description", "twitter:title", "twitter:description"):
        tag = soup.find("meta", attrs={"name": meta_key})
        if tag and tag.get("content"):
            tag["content"] = google_translate(tag["content"]).strip()
    for prop in ("og:title", "og:description", "og:site_name"):
        tag = soup.find("meta", attrs={"property": prop})
        if tag and tag.get("content"):
            tag["content"] = google_translate(tag["content"]).strip()

    skip_parents = {"script", "style", "svg", "path", "noscript", "code", "pre"}
    for node in list(soup.find_all(string=True)):
        if isinstance(node, Comment) or not node.parent or node.parent.name in skip_parents:
            continue
        raw = str(node)
        if should_translate(raw):
            node.replace_with(NavigableString(google_translate(raw)))

    for tag in soup.find_all(True):
        for attr in ("alt", "title", "aria-label", "placeholder"):
            value = tag.get(attr)
            if isinstance(value, str) and should_translate(value):
                tag[attr] = google_translate(value).strip()
        href = tag.get("href")
        if isinstance(href, str) and href.startswith(PROD_HOST):
            tag["href"] = REVIEW_HOST + href[len(PROD_HOST) :]

    if soup.body:
        review_css = soup.new_tag("style")
        review_css["id"] = "tns-korean-review-banner-style"
        review_css.string = (
            ".tns-korean-review-banner{position:fixed;left:10px;bottom:10px;z-index:9999;"
            "background:rgba(11,22,48,.92);color:#fff;padding:7px 10px;border-radius:7px;"
            "font:700 11px/1.2 system-ui,-apple-system,'Segoe UI',sans-serif;box-shadow:0 4px 16px rgba(0,0,0,.18)}"
        )
        if soup.head:
            soup.head.append(review_css)
        banner = soup.new_tag("div")
        banner["class"] = "tns-korean-review-banner"
        banner.string = "한글 검수판 · 검색 비노출"
        soup.body.append(banner)

    rendered = str(soup).replace(PROD_HOST, REVIEW_HOST)
    path.write_text(rendered, encoding="utf-8")


def translate_json_file(path: Path) -> None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return

    def walk(obj):
        if isinstance(obj, dict):
            return {k: walk(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [walk(v) for v in obj]
        if isinstance(obj, str):
            if obj.startswith(("http://", "https://")):
                return obj.replace(PROD_HOST, REVIEW_HOST)
            return google_translate(obj).strip() if should_translate(obj) else obj
        return obj

    path.write_text(json.dumps(walk(data), ensure_ascii=False, indent=2), encoding="utf-8")


def count_untranslated(paths: Iterable[Path]) -> list[dict[str, object]]:
    out = []
    for path in paths:
        if path.suffix.lower() not in {".html", ".json"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        hits = VI_DIACRITICS.findall(text)
        if hits:
            out.append({"path": path.relative_to(TARGET).as_posix(), "vietnamese_diacritic_chars": len(hits)})
    return out


def main() -> None:
    copy_source_site()
    html_paths = sorted(TARGET.glob("*.html")) + sorted((TARGET / "news").glob("*.html"))
    json_paths = sorted((TARGET / "news").glob("*.json"))

    strings: list[str] = []
    for path in html_paths:
        strings.extend(collect_html_strings(path))
    for path in json_paths:
        strings.extend(collect_json_strings(path))
    prime_cache(strings)

    for i, path in enumerate(html_paths, 1):
        print(f"[{i}/{len(html_paths)}] rendering Korean {path.relative_to(TARGET)}", flush=True)
        translate_html(path)
    for path in json_paths:
        translate_json_file(path)

    report = {
        "source_repo": "tnsuhak/XJTLU_Vietnam",
        "source_branch": "preview/homepage-youtube-7co9mt5a9yu-20260908",
        "source_commit": os.environ.get("SOURCE_COMMIT", "unknown"),
        "html_pages": len(html_paths),
        "unique_translations": len(cache),
        "translation_failures": failures,
        "untranslated_scan": count_untranslated(html_paths + json_paths),
        "review_policy": "noindex,nofollow + robots Disallow /",
    }
    (TARGET / "review-sync-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(f"Translation service failures: {len(failures)}")


if __name__ == "__main__":
    main()
