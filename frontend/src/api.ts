export interface WordItem {
  word: string
  count: number
  ratio: number
}

export interface AnalyzeResponse {
  words: WordItem[]
  total_tokens: number
  unique_words: number
  source: 'text' | 'gdocs'
  gdocs_tabs_fetched: number | null
}

export interface AnalyzeRequest {
  text?: string | null
  gdocs_url?: string | null
  min_count: number
  top_n: number
}

export async function analyzeText(request: AnalyzeRequest): Promise<AnalyzeResponse> {
  const response = await fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const detail = data.detail
    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((item: { msg?: string }) => item.msg).filter(Boolean).join(', ')
          : '분석 중 오류가 발생했습니다.'
    throw new Error(message || '분석 중 오류가 발생했습니다.')
  }

  return data as AnalyzeResponse
}
