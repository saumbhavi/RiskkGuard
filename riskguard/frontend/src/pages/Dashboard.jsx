import { useState } from 'react'
import OrderForm from '../components/OrderForm'
import CsvUpload from '../components/CsvUpload'
import ResultsTable from '../components/ResultsTable'
import { predictSingle, predictCsv } from '../api/client'

export default function Dashboard() {
  const [mode, setMode] = useState('single')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [results, setResults] = useState(null)
  const [summary, setSummary] = useState(null)

  async function handleSingle(order) {
    setLoading(true)
    setError(null)
    try {
      const res = await predictSingle(order)
      setResults([res])
      setSummary(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleCsv(file) {
    setLoading(true)
    setError(null)
    try {
      const res = await predictCsv(file)
      setResults(res.results)
      setSummary(res.summary)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <header className="border-b border-line bg-surface px-8 py-5">
        <h1 className="font-display text-[26px] text-ink">Order console</h1>
        <p className="text-[13px] text-ink-muted mt-1">
          Score an incoming order for return risk, or run a batch through a CSV export from your OMS.
        </p>
      </header>

      <div className="px-8 py-6 max-w-5xl">
        <div className="flex gap-1 mb-6 w-fit panel p-1">
          <TabButton active={mode === 'single'} onClick={() => setMode('single')}>
            Single order
          </TabButton>
          <TabButton active={mode === 'csv'} onClick={() => setMode('csv')}>
            CSV batch
          </TabButton>
        </div>

        <div className="panel p-6 mb-6">
          {mode === 'single' ? (
            <OrderForm onSubmit={handleSingle} loading={loading} />
          ) : (
            <CsvUpload onSubmit={handleCsv} loading={loading} />
          )}
        </div>

        {error && (
          <div className="mb-6 px-4 py-3 rounded bg-risk-highBg text-risk-high text-sm">
            Could not score this request: {error}
          </div>
        )}

        {results && <ResultsTable results={results} summary={summary} />}
      </div>
    </div>
  )
}

function TabButton({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`px-3.5 py-1.5 text-sm font-medium rounded transition-colors ${
        active ? 'bg-brand text-white' : 'text-ink-muted hover:text-ink'
      }`}
    >
      {children}
    </button>
  )
}
