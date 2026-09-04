const STYLES = {
  low: 'bg-risk-lowBg text-risk-low',
  medium: 'bg-risk-mediumBg text-risk-medium',
  high: 'bg-risk-highBg text-risk-high',
}

const LABELS = {
  low: 'Low',
  medium: 'Medium',
  high: 'High',
}

export default function RiskBadge({ tier }) {
  const cls = STYLES[tier] || 'bg-paper text-ink-muted'
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded text-[12px] font-medium ${cls}`}>
      {LABELS[tier] || tier}
    </span>
  )
}
