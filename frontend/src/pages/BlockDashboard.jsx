import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { fetchBlockSummary, fetchBlockSchools, fetchBlockChronic } from '../api';
import { KPICard, RiskBadge, StatusBadge, Loader } from '../components/Shared';

export default function BlockDashboard() {
  const { district, block } = useParams();
  const nav = useNavigate();
  const [summary, setSummary] = useState(null);
  const [schools, setSchools] = useState(null);
  const [chronic, setChronic] = useState(null);
  const [tab, setTab] = useState('all');

  useEffect(() => {
    fetchBlockSummary(district, block).then(setSummary);
    fetchBlockSchools(district, block).then(setSchools);
    fetchBlockChronic(district, block).then(setChronic);
  }, [district, block]);

  if (!summary) return <Loader />;

  const k = summary.kpis;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link to={`/district/${district}`} className="text-blue-600 hover:underline text-sm">← {district}</Link>
        <div>
          <h1 className="text-2xl font-bold">{block}</h1>
          <p className="text-sm text-gray-500">Block / Mandal Education Officer — {district}</p>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <KPICard label="Schools" value={k.total_schools} color="blue" />
        <KPICard label="Critical" value={k.critical} color="red" />
        <KPICard label="High" value={k.high} color="orange" />
        <KPICard label="Classroom Gap" value={k.total_classroom_gap} color="yellow" />
        <KPICard label="Teacher Gap" value={k.total_teacher_gap} color="purple" />
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b">
        {[['all', 'All Schools'], ['chronic', `Chronic (${chronic?.chronic?.length || 0})`], ['volatile', `Volatile (${chronic?.volatile?.length || 0})`]].map(([key, label]) => (
          <button key={key}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition ${tab === key ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
            onClick={() => setTab(key)}>
            {label}
          </button>
        ))}
      </div>

      {/* School List */}
      {tab === 'all' && (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-3 py-2">School</th>
                  <th className="text-center px-2 py-2">Risk</th>
                  <th className="text-right px-2 py-2">Score</th>
                  <th className="text-right px-2 py-2">Enrolment</th>
                  <th className="text-right px-2 py-2">CR Gap</th>
                  <th className="text-right px-2 py-2">TR Gap</th>
                  <th className="text-center px-2 py-2">Trend</th>
                  <th className="text-center px-2 py-2">Budget</th>
                  <th className="text-center px-2 py-2">Flags</th>
                </tr>
              </thead>
              <tbody>
                {schools?.schools?.map(s => (
                  <tr key={s.school_id} className="border-t hover:bg-blue-50 cursor-pointer"
                    onClick={() => nav(`/school/${s.school_id}`)}>
                    <td className="px-3 py-2 truncate max-w-[200px]">{s.school_name || s.school_id}</td>
                    <td className="px-2 py-2 text-center"><RiskBadge level={s.risk_level} /></td>
                    <td className="px-2 py-2 text-right font-mono">{s.risk_score?.toFixed(2)}</td>
                    <td className="px-2 py-2 text-right">{s.total_enrolment?.toLocaleString()}</td>
                    <td className="px-2 py-2 text-right">{s.classroom_gap}</td>
                    <td className="px-2 py-2 text-right">{s.teacher_gap}</td>
                    <td className="px-2 py-2 text-center text-xs">{s.trend_direction}</td>
                    <td className="px-2 py-2 text-center"><StatusBadge status={s.budget_status} /></td>
                    <td className="px-2 py-2 text-center">
                      {s.is_chronic ? <span title="Chronic" className="text-red-500">🔴</span> : ''}
                      {s.is_volatile ? <span title="Volatile" className="text-yellow-500">⚡</span> : ''}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'chronic' && (
        <div className="card overflow-hidden">
          <h3 className="font-semibold mb-3 text-red-600">Chronic High-Risk Schools (3+ years)</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-red-50">
                <tr>
                  <th className="text-left px-3 py-2">School</th>
                  <th className="text-right px-3 py-2">Risk Score</th>
                  <th className="text-center px-3 py-2">Trend</th>
                  <th className="text-right px-3 py-2">CR Gap</th>
                  <th className="text-right px-3 py-2">TR Gap</th>
                </tr>
              </thead>
              <tbody>
                {chronic?.chronic?.map(s => (
                  <tr key={s.school_id} className="border-t hover:bg-red-50 cursor-pointer"
                    onClick={() => nav(`/school/${s.school_id}`)}>
                    <td className="px-3 py-2">{s.school_name || s.school_id}</td>
                    <td className="px-3 py-2 text-right font-mono">{s.risk_score?.toFixed(3)}</td>
                    <td className="px-3 py-2 text-center">{s.trend_direction}</td>
                    <td className="px-3 py-2 text-right">{s.classroom_gap}</td>
                    <td className="px-3 py-2 text-right">{s.teacher_gap}</td>
                  </tr>
                ))}
                {!chronic?.chronic?.length && <tr><td colSpan={5} className="px-3 py-4 text-center text-gray-500">No chronic schools in this block</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'volatile' && (
        <div className="card overflow-hidden">
          <h3 className="font-semibold mb-3 text-yellow-600">Volatile Schools (|risk Δ| &gt; 0.15)</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-yellow-50">
                <tr>
                  <th className="text-left px-3 py-2">School</th>
                  <th className="text-right px-3 py-2">Risk Score</th>
                  <th className="text-right px-3 py-2">Risk Δ</th>
                  <th className="text-center px-3 py-2">Trend</th>
                </tr>
              </thead>
              <tbody>
                {chronic?.volatile?.map(s => (
                  <tr key={s.school_id} className="border-t hover:bg-yellow-50 cursor-pointer"
                    onClick={() => nav(`/school/${s.school_id}`)}>
                    <td className="px-3 py-2">{s.school_name || s.school_id}</td>
                    <td className="px-3 py-2 text-right font-mono">{s.risk_score?.toFixed(3)}</td>
                    <td className="px-3 py-2 text-right font-mono">{s.risk_delta?.toFixed(3)}</td>
                    <td className="px-3 py-2 text-center">{s.trend_direction}</td>
                  </tr>
                ))}
                {!chronic?.volatile?.length && <tr><td colSpan={4} className="px-3 py-4 text-center text-gray-500">No volatile schools in this block</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
