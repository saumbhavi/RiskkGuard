import { useRef, useState } from 'react'

export default function CsvUpload({ onSubmit, loading }) {
  const [fileName, setFileName] = useState(null)
  const [file, setFile] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const inputRef = useRef(null)

  function acceptFile(f) {
    if (!f) return
    setFile(f)
    setFileName(f.name)
  }

  function handleSubmit(e) {
    e.preventDefault()
    if (file) onSubmit(file)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div
        className={`border border-dashed rounded px-6 py-10 text-center transition-colors cursor-pointer ${
          dragActive ? 'border-brand bg-brand-light' : 'border-line hover:border-ink-faint'
        }`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault()
          setDragActive(true)
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragActive(false)
          acceptFile(e.dataTransfer.files?.[0])
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => acceptFile(e.target.files?.[0])}
        />
        <div className="text-sm text-ink">
          {fileName ? <span className="font-medium">{fileName}</span> : 'Drop a CSV of orders here, or click to browse'}
        </div>
        <div className="text-[12px] text-ink-faint mt-1">
          Required columns: category, payment_method, order_value. Any other order fields are optional.
        </div>
      </div>
      <button type="submit" className="btn-primary" disabled={loading || !file}>
        {loading ? 'Scoring batch…' : 'Score CSV batch'}
      </button>
    </form>
  )
}
