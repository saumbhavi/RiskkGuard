import { Fragment, useState } from 'react'
import RiskBadge from './RiskBadge'

export default function ResultsTable({ results, summary }) {
  const [expanded, setExpanded] = useState(null)

  if (!results || results.length === 0) return null

  return (
    <div>
      {summary && (
        <div className="grid grid-cols-4 gap-3 mb-4">
          <StatBox label="Orders scored" value={summary.total_orders} />
          <StatBox label="High risk" value={`${summary.high_risk} · ${summary.high_risk_pct}%`} tone="high" />
          <StatBox label="Medium risk" value={summary.medium_risk} tone="medium" />
          <StatBox label="Avg risk score" value={summary.avg_risk_score?.toFixed(3)} />
        </div>
      )}
      <div className="panel overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line bg-paper text-left text-[12px] text-ink-muted">
              <th className="px-4 py-2.5 font-medium">Order</th>
              <th className="px-4 py-2.5 font-medium">Risk score</th>
              <th className="px-4 py-2.5 font-medium">Tier</th>
              <th className="px-4 py-2.5 font-medium">Top reason</th>
              <th className="px-4 py-2.5 font-medium w-8"></th>
            </tr>
          </thead>
          <tbody>
            {results.map((r, i) => (
              <Fragment key={r.order_id}>
                <tr
                  className="border-b border-line last:border-0 hover:bg-paper/60 cursor-pointer"
                  onClick={() => setExpanded(expanded === i ? null : i)}
                >
                  <td className="px-4 py-2.5 font-mono text-[13px]">{r.order_id}</td>
                  <td className="px-4 py-2.5 font-mono text-[13px]">{r.risk_score.toFixed(3)}</td>
                  <td className="px-4 py-2.5">
                    <RiskBadge tier={r.risk_tier} />
                  </td>
                  <td className="px-4 py-2.5 text-ink-muted text-[13px]">{r.reason_codes[0]?.message}</td>
                  <td className="px-4 py-2.5 text-ink-faint text-[12px]">{expanded === i ? '−' : '+'}</td>
                </tr>
                {expanded === i && (
                  <tr className="border-b border-line last:border-0 bg-paper/40">
                    <td colSpan={5} className="px-4 py-3">
                      <div className="text-[12px] text-ink-muted font-medium mb-1.5">All contributing factors</div>
                      <ul className="space-y-1">
                        {r.reason_codes.map((rc) => (
                          <li key={rc.code} className="text-[13px] text-ink flex justify-between max-w-md">
                            <span>{rc.message}</span>
                          </li>
                        ))}
                      </ul>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function StatBox({ label, value, tone }) {
  const toneCls = tone === 'high' ? 'text-risk-high' : tone === 'medium' ? 'text-risk-medium' : 'text-ink'
  return (
    <div className="panel px-4 py-3">
      <div className="text-[12px] text-ink-muted mb-1">{label}</div>
      <div className={`text-xl font-display ${toneCls}`}>{value}</div>
    </div>
  )
}
