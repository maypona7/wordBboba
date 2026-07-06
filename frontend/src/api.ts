export interface WordItem {
  word: string
  count: number
  ratio: number
}

export interface AnalyzeResponse {
  words: WordItem[]
  total_tokens: number
  unique_words: number
  source: 'text' | 'gdocs' | 'gslides' | 'pdf'
  gdocs_tabs_fetched: number | null
}

export interface AnalyzeRequest {
  text?: string | null
  gdocs_url?: string | null
  gslides_url?: string | null
  min_count: number
  top_n: number
}

function parseError(data: unknown): string {
  const detail = (data as { detail?: unknown })?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item: { msg?: string }) => item.msg)
      .filter(Boolean)
      .join(', ')
  }
  return '분석 중 오류가 발생했습니다.'
}

async function handleResponse(response: Response): Promise<AnalyzeResponse> {
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(parseError(data) || '분석 중 오류가 발생했습니다.')
  }

  return data as AnalyzeResponse
}

export async function analyzeText(request: AnalyzeRequest): Promise<AnalyzeResponse> {
  const response = await fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  return handleResponse(response)
}

export async function analyzePdf(
  file: File,
  min_count: number,
  top_n: number,
): Promise<AnalyzeResponse> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('min_count', String(min_count))
  formData.append('top_n', String(top_n))

  const response = await fetch('/api/analyze/pdf', {
    method: 'POST',
    body: formData,
  })

  return handleResponse(response)
}
