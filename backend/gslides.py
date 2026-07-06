import re
from dataclasses import dataclass
from zipfile import BadZipFile, ZipFile
from io import BytesIO

import httpx
from bs4 import BeautifulSoup

SLIDES_ID_PATTERN = re.compile(
    r"docs\.google\.com/presentation/d/(?:e/)?([a-zA-Z0-9_-]+)"
)
ACCESS_DENIED_MESSAGE = (
    "프레젠테이션에 접근할 수 없습니다. "
    "'링크가 있는 모든 사용자 → 보기'로 공유했는지 확인하세요."
)
INVALID_URL_MESSAGE = "올바른 Google Slides URL이 아닙니다."
EMPTY_SLIDES_MESSAGE = "프레젠테이션에서 텍스트를 찾을 수 없습니다."
LOGIN_MARKERS = ("accounts.google.com", "sign in", "로그인", "signin")


@dataclass
class GSlidesFetchResult:
    text: str
    slides_fetched: int


def extract_slides_id(url: str) -> str:
    match = SLIDES_ID_PATTERN.search(url.strip())
    if not match:
        raise ValueError(INVALID_URL_MESSAGE)
    return match.group(1)


def _normalize_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _looks_like_login_page(content: str) -> bool:
    lowered = content.lower()
    return any(marker in lowered for marker in LOGIN_MARKERS)


def _extract_text_from_html(html: str) -> str:
    if _looks_like_login_page(html):
        raise PermissionError(ACCESS_DENIED_MESSAGE)

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "meta", "link"]):
        tag.decompose()

    chunks: list[str] = []
    for element in soup.find_all(["p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th", "span", "div"]):
        text = element.get_text(separator=" ", strip=True)
        if text and len(text) > 1:
            chunks.append(text)

    if not chunks:
        body_text = soup.get_text(separator="\n", strip=True)
        if body_text:
            chunks.append(body_text)

    return _normalize_text("\n\n".join(chunks))


def _extract_text_from_zip(data: bytes) -> str:
    try:
        with ZipFile(BytesIO(data)) as archive:
            chunks: list[str] = []
            for name in archive.namelist():
                if not name.endswith(".html"):
                    continue
                html = archive.read(name).decode("utf-8", errors="ignore")
                text = _extract_text_from_html(html)
                if text:
                    chunks.append(text)
            return _normalize_text("\n\n".join(chunks))
    except BadZipFile:
        return ""


def _split_slide_sections(text: str) -> list[str]:
    sections = [section.strip() for section in re.split(r"\n{3,}", text) if section.strip()]
    return sections if sections else ([text.strip()] if text.strip() else [])


def _export_urls(slides_id: str) -> list[str]:
    base = f"https://docs.google.com/presentation/d/{slides_id}"
    return [
        f"{base}/export/txt",
        f"{base}/export?format=txt",
        f"https://docs.google.com/feeds/download/presentations/Export?id={slides_id}&exportFormat=txt",
        f"{base}/export/html",
        f"{base}/export?format=html",
    ]


async def _fetch_export_text(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        response = await client.get(url)
    except httpx.HTTPError:
        return None

    if response.status_code in (403, 404):
        raise PermissionError(ACCESS_DENIED_MESSAGE)
    if response.status_code >= 400:
        return None

    content_type = (response.headers.get("content-type") or "").lower()
    data = response.content

    if "zip" in content_type or data[:2] == b"PK":
        text = _extract_text_from_zip(data)
        return text or None

    text = response.text
    if _looks_like_login_page(text):
        raise PermissionError(ACCESS_DENIED_MESSAGE)

    if "html" in content_type or "<html" in text.lower():
        return _extract_text_from_html(text) or None

    normalized = _normalize_text(text)
    return normalized or None


async def fetch_gslides_text(url: str) -> GSlidesFetchResult:
    slides_id = extract_slides_id(url)
    collected: list[str] = []

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=30.0,
        trust_env=False,
        headers={"User-Agent": "wordBboba/1.0"},
    ) as client:
        for export_url in _export_urls(slides_id):
            text = await _fetch_export_text(client, export_url)
            if text:
                collected.append(text)

    if not collected:
        raise ValueError(EMPTY_SLIDES_MESSAGE)

    merged_text = _normalize_text("\n\n".join(collected))
    sections = _split_slide_sections(merged_text)

    if not merged_text.strip():
        raise ValueError(EMPTY_SLIDES_MESSAGE)

    return GSlidesFetchResult(text=merged_text, slides_fetched=max(len(sections), 1))
