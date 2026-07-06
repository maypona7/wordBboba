import os
from typing import Literal

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from analyzer import analyze_text
from gdocs import fetch_gdocs_text
from gslides import fetch_gslides_text
from pdf import extract_text_from_pdf

app = FastAPI(title="wordBboba", version="1.0.0")

allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    text: str | None = None
    gdocs_url: str | None = None
    gslides_url: str | None = None
    min_count: int = Field(default=2, ge=1)
    top_n: int = Field(default=20, ge=1)


class WordItem(BaseModel):
    word: str
    count: int
    ratio: float


class AnalyzeResponse(BaseModel):
    words: list[WordItem]
    total_tokens: int
    unique_words: int
    source: Literal["text", "gdocs", "gslides", "pdf"]
    gdocs_tabs_fetched: int | None = None


@app.get("/")
def root():
    return {"status": "ok", "service": "wordBboba API"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    source: Literal["text", "gdocs", "gslides", "pdf"] = "text"
    gdocs_tabs_fetched: int | None = None
    text = ""

    if request.gslides_url and request.gslides_url.strip():
        try:
            fetch_result = await fetch_gslides_text(request.gslides_url.strip())
            text = fetch_result.text
            gdocs_tabs_fetched = fetch_result.slides_fetched
            source = "gslides"
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502,
                detail="Google Slides를 가져오는 중 네트워크 오류가 발생했습니다.",
            ) from exc
    elif request.gdocs_url and request.gdocs_url.strip():
        try:
            fetch_result = await fetch_gdocs_text(request.gdocs_url.strip())
            text = fetch_result.text
            gdocs_tabs_fetched = fetch_result.tabs_fetched
            source = "gdocs"
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502,
                detail="Google Docs를 가져오는 중 네트워크 오류가 발생했습니다.",
            ) from exc
    elif request.text and request.text.strip():
        text = request.text.strip()
    else:
        raise HTTPException(status_code=400, detail="텍스트 또는 Google URL을 입력해 주세요.")

    if not text:
        raise HTTPException(status_code=400, detail="분석할 텍스트가 없습니다.")

    result = analyze_text(text, min_count=request.min_count, top_n=request.top_n)

    return AnalyzeResponse(
        words=[
            WordItem(word=w.word, count=w.count, ratio=w.ratio) for w in result.words
        ],
        total_tokens=result.total_tokens,
        unique_words=result.unique_words,
        source=source,
        gdocs_tabs_fetched=gdocs_tabs_fetched,
    )


@app.post("/api/analyze/pdf", response_model=AnalyzeResponse)
async def analyze_pdf(
    file: UploadFile = File(...),
    min_count: int = Form(2),
    top_n: int = Form(20),
):
    if file.content_type not in ("application/pdf", "application/x-pdf"):
        filename = (file.filename or "").lower()
        if not filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="PDF 파일만 업로드할 수 있습니다.")

    data = await file.read()
    try:
        text = extract_text_from_pdf(data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if min_count < 1 or top_n < 1:
        raise HTTPException(status_code=400, detail="min_count와 top_n은 1 이상이어야 합니다.")

    result = analyze_text(text, min_count=min_count, top_n=top_n)

    return AnalyzeResponse(
        words=[
            WordItem(word=w.word, count=w.count, ratio=w.ratio) for w in result.words
        ],
        total_tokens=result.total_tokens,
        unique_words=result.unique_words,
        source="pdf",
        gdocs_tabs_fetched=None,
    )
