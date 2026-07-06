import re
from dataclasses import dataclass

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


def _extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "meta", "link"]):
        tag.decompose()

    chunks: list[str] = []
    for element in soup.find_all(["p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th", "span"]):
        text = element.get_text(separator=" ", strip=True)
        if text:
            chunks.append(text)

    if not chunks:
        body_text = soup.get_text(separator="\n", strip=True)
        if body_text:
            chunks.append(body_text)

    return _normalize_text("\n\n".join(chunks))


def _split_slide_sections(text: str) -> list[str]:
    sections = [section.strip() for section in re.split(r"\n{3,}", text) if section.strip()]
    return sections if sections else ([text.strip()] if text.strip() else [])


async def _fetch_export(client: httpx.AsyncClient, slides_id: str, fmt: str) -> str:
    url = f"https://docs.google.com/presentation/d/{slides_id}/export?format={fmt}"
    try:
        response = await client.get(url)
    except httpx.HTTPError as exc:
        raise PermissionError(ACCESS_DENIED_MESSAGE) from exc

    if response.status_code in (403, 404):
        raise PermissionError(ACCESS_DENIED_MESSAGE)
    if response.status_code >= 400:
        raise PermissionError(ACCESS_DENIED_MESSAGE)

    return response.text


async def fetch_gslides_text(url: str) -> GSlidesFetchResult:
    slides_id = extract_slides_id(url)

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=30.0,
        trust_env=False,
        headers={"User-Agent": "wordBboba/1.0"},
    ) as client:
        txt_content = await _fetch_export(client, slides_id, "txt")
        txt_normalized = _normalize_text(txt_content)
        txt_sections = _split_slide_sections(txt_normalized)

        html_content = await _fetch_export(client, slides_id, "html")
        html_text = _extract_text_from_html(html_content)
        html_sections = _split_slide_sections(html_text)

        if len(html_sections) > len(txt_sections):
            merged_text = "\n\n".join(html_sections)
            slides_fetched = len(html_sections)
        else:
            merged_text = "\n\n".join(txt_sections)
            slides_fetched = len(txt_sections)

    if not merged_text.strip():
        raise ValueError(EMPTY_SLIDES_MESSAGE)

    return GSlidesFetchResult(text=merged_text, slides_fetched=max(slides_fetched, 1))
