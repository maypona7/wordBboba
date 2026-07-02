# wordBboba

한국어 텍스트에서 자주 등장하는 단어를 추출하는 웹 앱입니다.

- 텍스트 직접 입력 또는 **Google Docs 링크** 지원
- Google Docs는 **모든 탭**의 텍스트를 합쳐서 분석
- **최소 등장 횟수**와 **상위 N개** 기준을 사용자가 설정

## 요구 사항

- Python 3.11+
- Node.js 18+

## 실행 방법

### 1. 백엔드

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2. 프론트엔드 (별도 터미널)

```bash
cd frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:5173` 을 엽니다.

## Netlify + Render 배포

Netlify는 **Python 함수를 지원하지 않습니다.** 프론트는 Netlify, API는 Render에 배포합니다.

### 1. Render (API)

1. [Render](https://render.com)에서 이 저장소 연결
2. `render.yaml` Blueprint로 `wordbboba-api` 서비스 생성
3. 배포 후 API URL 확인 (예: `https://wordbboba-api.onrender.com`)

### 2. Netlify (프론트 + API 프록시)

Netlify 대시보드 → **Site configuration → Environment variables**:

| Key | Value |
|-----|-------|
| `BACKEND_URL` | Render API URL (예: `https://wordbboba-api.onrender.com`) |

```bash
netlify deploy --prod
```

- 프론트: Netlify 정적 호스팅
- `/api/analyze`: TypeScript Netlify Function → Render API로 프록시

## Google Docs 사용 방법

1. Google Docs에서 **공유** 버튼 클릭
2. **「링크가 있는 모든 사용자」** → **「보기」** 로 설정
3. 문서 URL을 앱에 붙여넣기

OAuth 없이 공개 공유된 문서만 지원합니다.

## API

`POST /api/analyze`

```json
{
  "text": "분석할 텍스트",
  "gdocs_url": null,
  "min_count": 2,
  "top_n": 20
}
```

`text`와 `gdocs_url` 중 하나를 제공합니다. `gdocs_url`이 있으면 Google Docs를 우선 사용합니다.
