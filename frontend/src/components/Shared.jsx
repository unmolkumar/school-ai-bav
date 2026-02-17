export function KPICard({ label, value, sub, color = 'blue' }) {
  const colors = {
    blue: 'border-blue-500 bg-blue-50',
    red: 'border-red-500 bg-red-50',
    orange: 'border-orange-500 bg-orange-50',
    green: 'border-green-500 bg-green-50',
    yellow: 'border-yellow-500 bg-yellow-50',
    purple: 'border-purple-500 bg-purple-50',
  };
  return (
    <div className={`card border-l-4 ${colors[color] || colors.blue}`}>
      <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-bold mt-1">{typeof value === 'number' ? value.toLocaleString() : value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

export function RiskBadge({ level }) {
  const cls = {
    CRITICAL: 'badge-critical', HIGH: 'badge-high',
    MODERATE: 'badge-moderate', LOW: 'badge-low',
  };
  return <span className={cls[level] || 'text-xs text-gray-500'}>{level}</span>;
}

export function GradeBadge({ grade }) {
  const cls = { A: 'grade-a', B: 'grade-b', C: 'grade-c', D: 'grade-d', F: 'grade-f' };
  return (
    <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${cls[grade] || 'bg-gray-200'}`}>
      {grade}
    </span>
  );
}

export function TrendArrow({ delta }) {
  if (delta == null) return <span className="text-gray-400">—</span>;
  if (delta < -0.01) return <span className="text-green-600">▼ {Math.abs(delta).toFixed(3)}</span>;
  if (delta > 0.01) return <span className="text-red-600">▲ {delta.toFixed(3)}</span>;
  return <span className="text-gray-500">→ stable</span>;
}

export function StatusBadge({ status }) {
  const c = {
    ACCEPTED: 'bg-green-100 text-green-700',
    FLAGGED: 'bg-yellow-100 text-yellow-700',
    REJECTED: 'bg-red-100 text-red-700',
    PENDING: 'bg-gray-100 text-gray-600',
    FUNDED: 'bg-green-100 text-green-700',
    PARTIALLY_FUNDED: 'bg-yellow-100 text-yellow-700',
    UNFUNDED: 'bg-red-100 text-red-700',
  };
  return <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${c[status] || 'bg-gray-100'}`}>{status}</span>;
}

export function Loader() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
  );
}
