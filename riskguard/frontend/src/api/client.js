const BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

async function handle(res) {
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || JSON.stringify(body)
    } catch {
      // ignore parse failure, use statusText
    }
    throw new Error(detail)
  }
  return res.json()
}

export async function getHealth() {
  return handle(await fetch(`${BASE}/health`))
}

export async function getMetrics() {
  return handle(await fetch(`${BASE}/metrics`))
}

export async function predictSingle(order) {
  return handle(
    await fetch(`${BASE}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(order),
    }),
  )
}

export async function predictBatch(orders) {
  return handle(
    await fetch(`${BASE}/predict/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(orders),
    }),
  )
}

export async function predictCsv(file) {
  const form = new FormData()
  form.append('file', file)
  return handle(
    await fetch(`${BASE}/predict/csv`, {
      method: 'POST',
      body: form,
    }),
  )
}
