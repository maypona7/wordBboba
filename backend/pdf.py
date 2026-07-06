from io import BytesIO

from pypdf import PdfReader

MAX_PDF_SIZE = 10 * 1024 * 1024


def extract_text_from_pdf(data: bytes) -> str:
    if len(data) > MAX_PDF_SIZE:
        raise ValueError("PDF 파일 크기는 10MB 이하여야 합니다.")

    reader = PdfReader(BytesIO(data))
    chunks: list[str] = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            chunks.append(text)

    merged = "\n".join(chunks).strip()
    if not merged:
        raise ValueError("PDF에서 텍스트를 추출할 수 없습니다.")

    return merged
