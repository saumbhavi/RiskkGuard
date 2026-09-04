import { NavLink, Outlet } from 'react-router-dom'

const navItems = [
  { to: '/', label: 'Order Console', end: true },
  { to: '/metrics', label: 'Model Performance' },
]

export default function Layout() {
  return (
    <div className="min-h-screen flex">
      <aside className="w-60 shrink-0 border-r border-line bg-surface flex flex-col">
        <div className="px-5 py-6 border-b border-line">
          <div className="font-display text-[22px] leading-none text-ink">RiskGuard</div>
          <div className="text-[12px] text-ink-muted mt-1">Return-risk console</div>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `block px-3 py-2 rounded text-sm font-medium transition-colors ${
                  isActive ? 'bg-brand-light text-brand-dark' : 'text-ink-muted hover:bg-paper hover:text-ink'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-5 py-4 border-t border-line text-[12px] text-ink-faint leading-relaxed">
          Defense-only scoring.
          <br />
          No automated order actions are taken — every flag routes to a human decision.
        </div>
      </aside>
      <div className="flex-1 flex flex-col min-w-0">
        <Outlet />
      </div>
    </div>
  )
}
