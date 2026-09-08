from __future__ import annotations

import gc
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Iterable

import torch
from bs4 import BeautifulSoup, Comment, NavigableString
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

SOURCE = Path(sys.argv[1]).resolve()
TARGET = Path(sys.argv[2]).resolve()
REVIEW_HOST = "https://xjtlu-vietnam-kr.netlify.app"
PROD_HOST = "https://xjtlu-vietnam.netlify.app"
VI_EN_MODEL = "Helsinki-NLP/opus-mt-vi-en"
EN_KO_MODEL = "Helsinki-NLP/opus-mt-tc-big-en-ko"

SKIP_DIRS = {".git", ".github", "scripts", "__pycache__"}
COPY_FILE_SUFFIXES = {
    ".html", ".htm", ".json", ".png", ".jpg", ".jpeg", ".webp", ".svg", ".ico", ".gif", ".avif", ".webmanifest"
}

VI_DIACRITICS = re.compile(r"[ăâđêôơưĂÂĐÊÔƠƯàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵÀÁẢÃẠẰẮẲẴẶẦẤẨẪẬÈÉẺẼẸỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌỒỐỔỖỘỜỚỞỠỢÙÚỦŨỤỪỨỬỮỰỲÝỶỸỴ]")
VI_COMMON = re.compile(
    r"\b(viet nam|xjtlu viet nam|sinh vien|hoc phi|hoc bong|tuyen sinh|du hoc|trung quoc|nganh hoc|"
    r"doi song|cau lac bo|the thao|dieu kien|truong dai hoc|bang|nam hoc|tai sao|xem|tin tuc|nguon|"
    r"chinh thuc|lien he|hoi dap|viet|anh|tai|va|voi|cho|cua|mot|nhung|khong|duoc|tu)\b",
    re.I,
)
LETTER_RE = re.compile(r"[A-Za-zÀ-ỹ가-힣]")
HANGUL_RE = re.compile(r"[가-힣]")
SHORT_PROPER = re.compile(
    r"^(XJTLU|QS|THE|ARWU|C9|AI|STEM|IELTS|TOEFL|VND|RMB|GBP|USD|TNS|SOS|Zalo|SIP|XEC|HCMC|TP\. ?HCM)$",
    re.I,
)

# Human-reviewed/common UI vocabulary. These override machine translation.
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
    "Đóng menu": "메뉴 닫기",
    "Xem thêm": "더 보기",
}

POST_REPLACEMENTS = [
    ("서안교통리버풀대학교", "시안교통리버풀대학교"),
    ("시안 자오퉁-리버풀 대학교", "시안교통리버풀대학교"),
    ("시안 자오퉁 리버풀 대학교", "시안교통리버풀대학교"),
    ("시안자오퉁리버풀대학교", "시안교통리버풀대학교"),
    ("리버풀 대학교", "리버풀대학교"),
    ("쑤저우 중국", "중국 쑤저우"),
    ("호치민 시", "호치민시"),
    ("SOS 인터내셔널", "SOS International"),
    ("TNS 월드와이드", "TNS Worldwide"),
    ("XJTLU 베트남어", "XJTLU 베트남"),
]

cache: dict[str, str] = dict(MANUAL_EXACT)
intermediate_en: dict[str, str] = {}
model_errors: list[dict[str, str]] = []


def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def should_translate(text: str) -> bool:
    t = normalize_ws(text)
    if not t or not LETTER_RE.search(t):
        return False
    if HANGUL_RE.search(t) and not VI_DIACRITICS.search(t):
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


def is_vietnamese(text: str) -> bool:
    t = normalize_ws(text)
    return bool(VI_DIACRITICS.search(t) or VI_COMMON.search(t))


def postprocess(text: str) -> str:
    out = text
    for a, b in POST_REPLACEMENTS:
        out = out.replace(a, b)
    return out


def split_for_model(text: str, max_chars: int = 900) -> list[str]:
    text = normalize_ws(text)
    if len(text) <= max_chars:
        return [text]
    sentences = re.split(r"(?<=[.!?。！？])\s+", text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > max_chars:
            words = sentence.split()
            for word in words:
                candidate = (current + " " + word).strip()
                if len(candidate) > max_chars and current:
                    chunks.append(current)
                    current = word
                else:
                    current = candidate
            continue
        candidate = (current + " " + sentence).strip()
        if len(candidate) > max_chars and current:
            chunks.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks or [text]


def load_model(name: str):
    print(f"Loading translation model: {name}", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(name)
    model = AutoModelForSeq2SeqLM.from_pretrained(name)
    model.eval()
    return tokenizer, model


def translate_with_model(tokenizer, model, texts: list[str], batch_size: int = 12) -> list[str]:
    outputs: list[str] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        encoded = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=512)
        with torch.inference_mode():
            generated = model.generate(
                **encoded,
                max_new_tokens=512,
                num_beams=3,
                early_stopping=True,
            )
        outputs.extend(tokenizer.batch_decode(generated, skip_special_tokens=True))
        done = min(start + batch_size, len(texts))
        if done % 120 < batch_size or done == len(texts):
            print(f"  model translated {done}/{len(texts)} chunks", flush=True)
    return outputs


def translate_map_with_model(tokenizer, model, items: dict[str, str]) -> dict[str, str]:
    keys: list[str] = []
    chunks: list[str] = []
    for key, value in items.items():
        parts = split_for_model(value)
        for idx, part in enumerate(parts):
            keys.append(f"{key}\u241f{idx}\u241f{len(parts)}")
            chunks.append(part)
    translated_chunks = translate_with_model(tokenizer, model, chunks)
    grouped: dict[str, list[tuple[int, str]]] = {}
    for compound, translated in zip(keys, translated_chunks):
        key, idx, _total = compound.rsplit("\u241f", 2)
        grouped.setdefault(key, []).append((int(idx), translated.strip()))
    result: dict[str, str] = {}
    for key, parts in grouped.items():
        result[key] = " ".join(text for _, text in sorted(parts)).strip()
    return result


def prime_cache(strings: Iterable[str]) -> None:
    unique: list[str] = []
    seen = set(cache)
    for raw in strings:
        t = normalize_ws(raw)
        if not should_translate(t) or t in seen:
            continue
        seen.add(t)
        unique.append(t)

    vi_strings = {t: t for t in unique if is_vietnamese(t)}
    en_strings = {t: t for t in unique if t not in vi_strings}
    print(
        f"Preparing {len(unique)} unique strings: {len(vi_strings)} Vietnamese, {len(en_strings)} English/mixed",
        flush=True,
    )

    # Stage 1: Vietnamese -> English.
    if vi_strings:
        vi_tokenizer, vi_model = load_model(VI_EN_MODEL)
        try:
            intermediate_en.update(translate_map_with_model(vi_tokenizer, vi_model, vi_strings,))
        except Exception as exc:  # noqa: BLE001
            model_errors.append({"stage": "vi-en", "error": repr(exc)})
            raise
        finally:
            del vi_model, vi_tokenizer
            gc.collect()

    # Stage 2: English -> Korean. Vietnamese strings use their English intermediate form;
    # already-English strings go directly to the English->Korean model.
    stage2: dict[str, str] = {}
    for source in unique:
        stage2[source] = intermediate_en.get(source, source)

    en_tokenizer, en_model = load_model(EN_KO_MODEL)
    try:
        ko_map = translate_map_with_model(en_tokenizer, en_model, stage2)
    except Exception as exc:  # noqa: BLE001
        model_errors.append({"stage": "en-ko", "error": repr(exc)})
        raise
    finally:
        del en_model, en_tokenizer
        gc.collect()

    for source, translated in ko_map.items():
        cache[source] = postprocess(translated)
    print(f"Translation cache ready: {len(cache)} strings", flush=True)


def korean_translate(text: str) -> str:
    raw = text
    t = normalize_ws(raw)
    if not should_translate(t):
        return raw
    leading = raw[: len(raw) - len(raw.lstrip())]
    trailing = raw[len(raw.rstrip()) :]
    translated = cache.get(t, t)
    return leading + postprocess(translated) + trailing


def copy_source_site() -> None:
    # Replace the review site's generated public content while preserving this branch's tooling.
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

    # Human-review mirror: never make it an indexable duplicate of the Vietnamese site.
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


def translate_html(path: Path) -> None:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    if soup.html:
        soup.html["lang"] = "ko"
    strip_indexing_metadata(soup)

    if soup.title and soup.title.string:
        title = korean_translate(str(soup.title.string)).strip()
        if not title.startswith("[한글 검수판]"):
            title = "[한글 검수판] " + title
        soup.title.string.replace_with(title)

    for meta_key in ("description", "twitter:title", "twitter:description"):
        tag = soup.find("meta", attrs={"name": meta_key})
        if tag and tag.get("content"):
            tag["content"] = korean_translate(tag["content"]).strip()
    for prop in ("og:title", "og:description", "og:site_name"):
        tag = soup.find("meta", attrs={"property": prop})
        if tag and tag.get("content"):
            tag["content"] = korean_translate(tag["content"]).strip()

    skip_parents = {"script", "style", "svg", "path", "noscript", "code", "pre"}
    for node in list(soup.find_all(string=True)):
        if isinstance(node, Comment) or not node.parent or node.parent.name in skip_parents:
            continue
        raw = str(node)
        if should_translate(raw):
            node.replace_with(NavigableString(korean_translate(raw)))

    for tag in soup.find_all(True):
        for attr in ("alt", "title", "aria-label", "placeholder"):
            value = tag.get(attr)
            if isinstance(value, str) and should_translate(value):
                tag[attr] = korean_translate(value).strip()
        href = tag.get("href")
        if isinstance(href, str) and href.startswith(PROD_HOST):
            tag["href"] = REVIEW_HOST + href[len(PROD_HOST) :]

    # Small marker so reviewers always know this is the Korean inspection copy.
    if soup.body:
        review_css = soup.new_tag("style")
        review_css["id"] = "tns-korean-review-banner-style"
        review_css.string = (
            ".tns-korean-review-banner{position:fixed;left:10px;bottom:10px;z-index:9999;"
            "background:rgba(11,22,48,.92);color:#fff;padding:7px 10px;border-radius:7px;"
            "font:700 11px/1.2 system-ui,-apple-system,'Segoe UI',sans-serif;"
            "box-shadow:0 4px 16px rgba(0,0,0,.18)}"
        )
        if soup.head:
            soup.head.append(review_css)
        banner = soup.new_tag("div")
        banner["class"] = "tns-korean-review-banner"
        banner.string = "한글 검수판 · 검색 비노출"
        soup.body.append(banner)

    rendered = str(soup).replace(PROD_HOST, REVIEW_HOST)
    path.write_text(rendered, encoding="utf-8")


def visible_untranslated_report(paths: Iterable[Path]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    skip_parents = {"script", "style", "svg", "path", "noscript", "code", "pre"}
    for path in paths:
        soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
        examples: list[str] = []
        count = 0
        for node in soup.find_all(string=True):
            if isinstance(node, Comment) or not node.parent or node.parent.name in skip_parents:
                continue
            text = normalize_ws(str(node))
            if text and VI_DIACRITICS.search(text):
                count += 1
                if len(examples) < 5:
                    examples.append(text[:180])
        if count:
            out.append({
                "path": path.relative_to(TARGET).as_posix(),
                "visible_vietnamese_text_nodes": count,
                "examples": examples,
            })
    return out


def main() -> None:
    torch.set_num_threads(max(1, min(4, os.cpu_count() or 2)))
    copy_source_site()
    html_paths = sorted(TARGET.glob("*.html")) + sorted((TARGET / "news").glob("*.html"))
    if len(html_paths) != 24:
        raise SystemExit(f"Expected 24 source HTML pages, got {len(html_paths)}")

    strings: list[str] = []
    for path in html_paths:
        strings.extend(collect_html_strings(path))
    prime_cache(strings)

    for i, path in enumerate(html_paths, 1):
        print(f"[{i}/{len(html_paths)}] rendering Korean {path.relative_to(TARGET)}", flush=True)
        translate_html(path)

    untranslated = visible_untranslated_report(html_paths)
    report = {
        "source_repo": "tnsuhak/XJTLU_Vietnam",
        "source_branch": "preview/homepage-youtube-7co9mt5a9yu-20260908",
        "source_commit": os.environ.get("SOURCE_COMMIT", "unknown"),
        "translation_backend": "offline Hugging Face Marian: vi-en -> en-ko",
        "html_pages": len(html_paths),
        "unique_translations": len(cache),
        "model_errors": model_errors,
        "visible_untranslated_scan": untranslated,
        "review_policy": "noindex,nofollow + robots Disallow /",
    }
    (TARGET / "review-sync-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    if model_errors:
        raise SystemExit(f"Translation model errors: {model_errors}")


if __name__ == "__main__":
    main()
