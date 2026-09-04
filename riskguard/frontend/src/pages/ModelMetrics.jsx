import { useEffect, useState } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { getMetrics } from '../api/client'

export default function ModelMetrics() {
  const [metrics, setMetrics] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getMetrics().then(setMetrics).catch((e) => setError(e.message))
  }, [])

  if (error) {
    return (
      <div className="p-8">
        <div className="px-4 py-3 rounded bg-risk-highBg text-risk-high text-sm max-w-lg">
          Could not load model metrics: {error}. Has the model been trained? Run{' '}
          <code className="font-mono">python -m app.ml.train</code> in the backend.
        </div>
      </div>
    )
  }
  if (!metrics) {
    return <div className="p-8 text-ink-muted text-sm">Loading held-out evaluation…</div>
  }

  const { headline, dataset, cost_curve, pr_curve, feature_importance, cost_assumptions } = metrics
  const cm = headline.confusion_matrix

  return (
    <div className="flex-1 overflow-y-auto">
      <header className="border-b border-line bg-surface px-8 py-5">
        <h1 className="font-display text-[26px] text-ink">Model performance</h1>
        <p className="text-[13px] text-ink-muted mt-1">
          Evaluated on a {dataset.n_test.toLocaleString()}-order held-out set (
          {dataset.test_date_range[0]} to {dataset.test_date_range[1]}), trained only on orders before it —
          a time-based split, not a random one.
        </p>
      </header>

      <div className="px-8 py-6 max-w-5xl space-y-8">
        <section>
          <div className="grid grid-cols-4 gap-3">
            <Headline label="Precision @ threshold" value={headline.precision_at_threshold.toFixed(3)} />
            <Headline label="Recall @ threshold" value={headline.recall_at_threshold.toFixed(3)} />
            <Headline label="ROC-AUC" value={headline.roc_auc.toFixed(3)} />
            <Headline
              label="Est. net value (test set)"
              value={`₹${headline.estimated_net_value_inr_on_test_set.toLocaleString('en-IN')}`}
            />
          </div>
          <p className="text-[12px] text-ink-faint mt-3 max-w-2xl">
            Operating threshold {headline.operating_threshold} was chosen to maximize net value, not F1 — see
            cost assumptions below. Base return rate in this evaluation window was{' '}
            {(dataset.base_return_rate * 100).toFixed(1)}%.
          </p>
        </section>

        <section>
          <SectionTitle>Confusion matrix @ operating threshold</SectionTitle>
          <div className="grid grid-cols-2 gap-2 max-w-md">
            <Cell label="True positive" sub="Correctly flagged returns" value={cm.tp} tone="low" />
            <Cell label="False positive" sub="Friction on a good order" value={cm.fp} tone="high" />
            <Cell label="False negative" sub="Return missed" value={cm.fn} tone="medium" />
            <Cell label="True negative" sub="Correctly left alone" value={cm.tn} tone="low" />
          </div>
        </section>

        <section>
          <SectionTitle>Cost curve — net value by threshold</SectionTitle>
          <p className="text-[12px] text-ink-muted mb-3 max-w-2xl">
            Assumes ₹{cost_assumptions.avg_return_cost_saved_per_tp} saved per correctly-flagged return and ₹
            {cost_assumptions.avg_friction_cost_per_fp} friction cost per false flag on a good order — edit
            these in <code className="font-mono">train.py</code> to match your merchant's real economics.
          </p>
          <div className="panel p-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={cost_curve} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid stroke="#DEE1E6" vertical={false} />
                <XAxis dataKey="threshold" tick={{ fontSize: 11, fill: '#5B6472' }} />
                <YAxis tick={{ fontSize: 11, fill: '#5B6472' }} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
                <Tooltip
                  formatter={(v) => [`₹${Number(v).toLocaleString('en-IN')}`, 'Net value']}
                  labelFormatter={(l) => `Threshold ${l}`}
                  contentStyle={{ fontSize: 12, borderRadius: 6, borderColor: '#DEE1E6' }}
                />
                <ReferenceLine x={headline.operating_threshold} stroke="#1B4D3E" strokeDasharray="4 3" />
                <Line type="monotone" dataKey="net_value_inr" stroke="#1B4D3E" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section>
          <SectionTitle>Precision–recall trade-off</SectionTitle>
          <div className="panel p-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={pr_curve} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid stroke="#DEE1E6" vertical={false} />
                <XAxis dataKey="recall" tick={{ fontSize: 11, fill: '#5B6472' }} label={{ value: 'Recall', position: 'insideBottom', offset: -2, fontSize: 11, fill: '#5B6472' }} />
                <YAxis domain={[0, 1]} tick={{ fontSize: 11, fill: '#5B6472' }} label={{ value: 'Precision', angle: -90, position: 'insideLeft', fontSize: 11, fill: '#5B6472' }} />
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 6, borderColor: '#DEE1E6' }} />
                <Line type="monotone" dataKey="precision" stroke="#B8862B" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="pb-10">
          <SectionTitle>What drives the score</SectionTitle>
          <div className="panel p-4 space-y-2.5">
            {feature_importance.slice(0, 8).map((f) => (
              <div key={f.feature} className="flex items-center gap-3">
                <div className="w-40 text-[12px] text-ink-muted shrink-0">{prettyFeature(f.feature)}</div>
                <div className="flex-1 bg-paper rounded h-2 overflow-hidden">
                  <div className="h-full bg-brand rounded" style={{ width: `${Math.min(f.importance_pct * 2, 100)}%` }} />
                </div>
                <div className="w-12 text-right text-[12px] font-mono text-ink-muted">{f.importance_pct}%</div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

function Headline({ label, value }) {
  return (
    <div className="panel px-4 py-3">
      <div className="text-[12px] text-ink-muted mb-1">{label}</div>
      <div className="text-xl font-display text-ink">{value}</div>
    </div>
  )
}

function SectionTitle({ children }) {
  return <h2 className="font-display text-[18px] text-ink mb-3">{children}</h2>
}

function Cell({ label, sub, value, tone }) {
  const toneCls = { low: 'text-risk-low', medium: 'text-risk-medium', high: 'text-risk-high' }[tone] || 'text-ink'
  return (
    <div className="panel px-4 py-3">
      <div className="text-[13px] text-ink font-medium">{label}</div>
      <div className="text-[11px] text-ink-faint mb-1.5">{sub}</div>
      <div className={`text-2xl font-display ${toneCls}`}>{value.toLocaleString()}</div>
    </div>
  )
}

function prettyFeature(f) {
  const map = {
    price_deviation_pct: 'Price deviation from category',
    pay_cod: 'Cash on delivery',
    discount_pct: 'Discount depth',
    customer_return_rate: 'Customer return history',
    delivery_delay_days: 'Delivery delay',
    customer_tenure_days: 'Customer tenure',
    seller_rating: 'Seller rating',
    cat_fashion: 'Fashion category',
  }
  return map[f] || f.replace(/^cat_/, '').replace(/^pay_/, '').replace(/_/g, ' ')
}
