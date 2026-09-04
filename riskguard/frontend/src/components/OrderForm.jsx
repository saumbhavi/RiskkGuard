import { useState } from 'react'

const CATEGORIES = ['fashion', 'electronics', 'home', 'beauty', 'grocery', 'other']
const PAYMENT_METHODS = [
  { value: 'cod', label: 'Cash on delivery' },
  { value: 'prepaid_card', label: 'Prepaid — card' },
  { value: 'upi', label: 'Prepaid — UPI' },
  { value: 'wallet', label: 'Prepaid — wallet' },
]

const DEFAULTS = {
  order_id: '',
  category: 'fashion',
  payment_method: 'cod',
  order_value: 2400,
  discount_pct: 20,
  customer_tenure_days: 120,
  customer_past_orders: 4,
  customer_past_returns: 0,
  seller_rating: 4.3,
  delivery_days: 4,
  promised_delivery_days: 3,
  is_weekend_purchase: 0,
  hour_of_day: 14,
  distance_km: 80,
}

export default function OrderForm({ onSubmit, loading }) {
  const [form, setForm] = useState(DEFAULTS)

  function update(key, value) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  function handleSubmit(e) {
    e.preventDefault()
    const payload = {
      ...form,
      order_id: form.order_id || undefined,
      order_value: Number(form.order_value),
      discount_pct: Number(form.discount_pct),
      customer_tenure_days: Number(form.customer_tenure_days),
      customer_past_orders: Number(form.customer_past_orders),
      customer_past_returns: Number(form.customer_past_returns),
      seller_rating: Number(form.seller_rating),
      delivery_days: Number(form.delivery_days),
      promised_delivery_days: Number(form.promised_delivery_days),
      is_weekend_purchase: Number(form.is_weekend_purchase),
      hour_of_day: Number(form.hour_of_day),
      distance_km: Number(form.distance_km),
    }
    onSubmit(payload)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="field-label">Order ID</label>
          <input
            className="field-input"
            placeholder="Auto-generated if left blank"
            value={form.order_id}
            onChange={(e) => update('order_id', e.target.value)}
          />
        </div>
        <div>
          <label className="field-label">Order value (₹)</label>
          <input
            type="number"
            min="1"
            className="field-input"
            value={form.order_value}
            onChange={(e) => update('order_value', e.target.value)}
            required
          />
        </div>
        <div>
          <label className="field-label">Category</label>
          <select className="field-input" value={form.category} onChange={(e) => update('category', e.target.value)}>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c[0].toUpperCase() + c.slice(1)}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="field-label">Payment method</label>
          <select className="field-input" value={form.payment_method} onChange={(e) => update('payment_method', e.target.value)}>
            {PAYMENT_METHODS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="field-label">Discount (%)</label>
          <input
            type="number"
            min="0"
            max="100"
            className="field-input"
            value={form.discount_pct}
            onChange={(e) => update('discount_pct', e.target.value)}
          />
        </div>
        <div>
          <label className="field-label">Seller rating (1–5)</label>
          <input
            type="number"
            step="0.1"
            min="1"
            max="5"
            className="field-input"
            value={form.seller_rating}
            onChange={(e) => update('seller_rating', e.target.value)}
          />
        </div>
        <div>
          <label className="field-label">Customer tenure (days)</label>
          <input
            type="number"
            min="0"
            className="field-input"
            value={form.customer_tenure_days}
            onChange={(e) => update('customer_tenure_days', e.target.value)}
          />
        </div>
        <div>
          <label className="field-label">Distance to customer (km)</label>
          <input
            type="number"
            min="0"
            className="field-input"
            value={form.distance_km}
            onChange={(e) => update('distance_km', e.target.value)}
          />
        </div>
        <div>
          <label className="field-label">Past orders</label>
          <input
            type="number"
            min="0"
            className="field-input"
            value={form.customer_past_orders}
            onChange={(e) => update('customer_past_orders', e.target.value)}
          />
        </div>
        <div>
          <label className="field-label">Past returns</label>
          <input
            type="number"
            min="0"
            className="field-input"
            value={form.customer_past_returns}
            onChange={(e) => update('customer_past_returns', e.target.value)}
          />
        </div>
        <div>
          <label className="field-label">Promised delivery (days)</label>
          <input
            type="number"
            min="0"
            className="field-input"
            value={form.promised_delivery_days}
            onChange={(e) => update('promised_delivery_days', e.target.value)}
          />
        </div>
        <div>
          <label className="field-label">Actual delivery (days)</label>
          <input
            type="number"
            min="0"
            className="field-input"
            value={form.delivery_days}
            onChange={(e) => update('delivery_days', e.target.value)}
          />
        </div>
        <div>
          <label className="field-label">Hour of purchase (0–23)</label>
          <input
            type="number"
            min="0"
            max="23"
            className="field-input"
            value={form.hour_of_day}
            onChange={(e) => update('hour_of_day', e.target.value)}
          />
        </div>
        <div className="flex items-end pb-2.5">
          <label className="flex items-center gap-2 text-sm text-ink-muted">
            <input
              type="checkbox"
              checked={Boolean(form.is_weekend_purchase)}
              onChange={(e) => update('is_weekend_purchase', e.target.checked ? 1 : 0)}
              className="rounded border-line"
            />
            Weekend purchase
          </label>
        </div>
      </div>
      <button type="submit" className="btn-primary" disabled={loading}>
        {loading ? 'Scoring…' : 'Score order'}
      </button>
    </form>
  )
}
