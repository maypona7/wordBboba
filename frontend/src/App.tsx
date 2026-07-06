import { useState, type FormEvent, type ChangeEvent } from 'react'
import { analyzeText, analyzePdf, type AnalyzeResponse } from './api'
import './App.css'

type InputMode = 'text' | 'gdocs' | 'gslides' | 'pdf'

function App() {
  const [inputMode, setInputMode] = useState<InputMode>('text')
  const [text, setText] = useState('')
  const [gdocsUrl, setGdocsUrl] = useState('')
  const [gslidesUrl, setGslidesUrl] = useState('')
  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [minCount, setMinCount] = useState(2)
  const [topN, setTopN] = useState(20)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const [copied, setCopied] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)
    setCopied(false)

    try {
      const response =
        inputMode === 'pdf'
          ? await analyzePdf(pdfFile!, minCount, topN)
          : await analyzeText({
              text: inputMode === 'text' ? text : null,
              gdocs_url: inputMode === 'gdocs' ? gdocsUrl : null,
              gslides_url: inputMode === 'gslides' ? gslidesUrl : null,
              min_count: minCount,
              top_n: topN,
            })
      setResult(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : '분석 중 오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  async function handleCopy() {
    if (!result || result.words.length === 0) return

    const text = result.words.map((item) => item.word).join(',')
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  function handlePdfChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null
    setPdfFile(file)
  }

  const maxCount = result?.words[0]?.count ?? 1
  const submitDisabled = loading || (inputMode === 'pdf' && !pdfFile)

  return (
    <div className="app">
      <header className="header">
        <h1>wordBboba</h1>
      </header>

      <form className="panel" onSubmit={handleSubmit}>
        <div className="tabs">
          <button
            type="button"
            className={inputMode === 'text' ? 'tab active' : 'tab'}
            onClick={() => setInputMode('text')}
          >
            직접 입력
          </button>
          <button
            type="button"
            className={inputMode === 'gdocs' ? 'tab active' : 'tab'}
            onClick={() => setInputMode('gdocs')}
          >
            Google Docs
          </button>
          <button
            type="button"
            className={inputMode === 'gslides' ? 'tab active' : 'tab'}
            onClick={() => setInputMode('gslides')}
          >
            Google Slides
          </button>
          <button
            type="button"
            className={inputMode === 'pdf' ? 'tab active' : 'tab'}
            onClick={() => setInputMode('pdf')}
          >
            PDF
          </button>
        </div>

        {inputMode === 'text' ? (
          <label className="field">
            <span>텍스트</span>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="분석할 한국어 텍스트를 입력하세요."
              rows={10}
            />
          </label>
        ) : inputMode === 'gdocs' ? (
          <label className="field">
            <span>Google Docs URL</span>
            <input
              type="url"
              value={gdocsUrl}
              onChange={(e) => setGdocsUrl(e.target.value)}
              placeholder="https://docs.google.com/document/d/..."
            />
          </label>
        ) : inputMode === 'gslides' ? (
          <label className="field">
            <span>Google Slides URL</span>
            <input
              type="url"
              value={gslidesUrl}
              onChange={(e) => setGslidesUrl(e.target.value)}
              placeholder="https://docs.google.com/presentation/d/..."
            />
          </label>
        ) : (
          <label className="field">
            <span>PDF 파일</span>
            <input
              type="file"
              accept="application/pdf,.pdf"
              onChange={handlePdfChange}
            />
            {pdfFile && <span className="file-name">{pdfFile.name}</span>}
          </label>
        )}

        <div className="settings">
          <label className="field inline">
            <span>최소 등장 횟수</span>
            <input
              type="number"
              min={1}
              value={minCount}
              onChange={(e) => setMinCount(Number(e.target.value))}
            />
          </label>
          <label className="field inline">
            <span>상위 N개</span>
            <input
              type="number"
              min={1}
              value={topN}
              onChange={(e) => setTopN(Number(e.target.value))}
            />
          </label>
        </div>

        <button type="submit" className="submit" disabled={submitDisabled}>
          {loading ? '분석 중…' : '분석하기'}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      {result && (
        <section className="results">
          <div className="summary">
            <div className="summary-stats">
              <span>총 토큰: {result.total_tokens.toLocaleString()}</span>
              <span>고유 단어: {result.unique_words.toLocaleString()}</span>
            </div>
            {result.words.length > 0 && (
              <button type="button" className="copy" onClick={handleCopy}>
                {copied ? '복사됨' : '복사'}
              </button>
            )}
          </div>

          {result.words.length === 0 ? (
            <p className="empty">조건에 맞는 단어가 없습니다. 기준을 낮춰 보세요.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>순위</th>
                  <th>단어</th>
                  <th>횟수</th>
                  <th>비율</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {result.words.map((item, index) => (
                  <tr key={item.word}>
                    <td>{index + 1}</td>
                    <td className="word">{item.word}</td>
                    <td>{item.count}</td>
                    <td>{(item.ratio * 100).toFixed(1)}%</td>
                    <td className="bar-cell">
                      <div
                        className="bar"
                        style={{ width: `${(item.count / maxCount) * 100}%` }}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}
    </div>
  )
}

export default App
