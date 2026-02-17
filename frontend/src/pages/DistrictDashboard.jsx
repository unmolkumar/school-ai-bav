import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { fetchDistrictCompliance, fetchDistrictBlocks, fetchDistrictPriority, fetchDistrictProposals } from '../api';
import { KPICard, GradeBadge, TrendArrow, RiskBadge, StatusBadge, Loader } from '../components/Shared';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, PieChart, Pie, Cell, Legend } from 'recharts';

const RISK_COLORS = { CRITICAL: '#ef4444', HIGH: '#f97316', MODERATE: '#eab308', LOW: '#22c55e' };
const DEC_COLORS = { ACCEPTED: '#22c55e', FLAGGED: '#eab308', REJECTED: '#ef4444' };

export default function DistrictDashboard() {
  const { name } = useParams();
  const nav = useNavigate();
  const [compliance, setCompliance] = useState(null);
  const [blocks, setBlocks] = useState(null);
  const [priority, setPriority] = useState(null);
  const [proposals, setProposals] = useState(null);

  useEffect(() => {
    fetchDistrictCompliance(name).then(setCompliance);
    fetchDistrictBlocks(name).then(setBlocks);
    fetchDistrictPriority(name).then(setPriority);
    fetchDistrictProposals(name).then(setProposals);
  }, [name]);

  if (!compliance) return <Loader />;

  const latest = compliance[compliance.length - 1] || {};

  const proposalPie = proposals?.summary?.map(s => ({
    name: s.decision_status, value: s.count,
  })) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link to="/state" className="text-blue-600 hover:underline text-sm">← State</Link>
        <div>
          <h1 className="text-2xl font-bold">{name}</h1>
          <p className="text-sm text-gray-500">District Education Officer Dashboard</p>
        </div>
      </div>

      {/* Compliance Card + KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="card flex items-center gap-4">
          <GradeBadge grade={latest.compliance_grade} />
          <div>
            <p className="text-xs text-gray-500">Grade</p>
            <p className="text-lg font-bold">{latest.compliance_grade}</p>
          </div>
        </div>
        <KPICard label="State Rank" value={`#${latest.district_rank}`} color="blue" />
        <KPICard label="Avg Risk" value={latest.avg_risk_score?.toFixed(3)} color="orange" />
        <KPICard label="YoY Change" value={<TrendArrow delta={latest.yoy_risk_improvement} />} color="green" />
        <KPICard label="Schools" value={latest.total_schools} color="purple" />
      </div>

      {/* Trend + Block Heatmap */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* District Trend */}
        <div className="card">
          <h3 className="font-semibold mb-3">District Risk Trend (7yr)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={compliance}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="academic_year" tick={{ fontSize: 10 }} />
              <YAxis domain={[0, 0.5]} tick={{ fontSize: 10 }} />
              <Tooltip />
              <Line type="monotone" dataKey="avg_risk_score" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} name="Risk Score" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Block Heatmap Table */}
        <div className="card overflow-hidden">
          <h3 className="font-semibold mb-3">Block-wise Risk Distribution</h3>
          <div className="overflow-x-auto max-h-72">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 sticky top-0">
                <tr>
                  <th className="text-left px-3 py-2">Block</th>
                  <th className="text-center px-2 py-2 text-red-600">Crit</th>
                  <th className="text-center px-2 py-2 text-orange-600">High</th>
                  <th className="text-center px-2 py-2 text-yellow-600">Mod</th>
                  <th className="text-center px-2 py-2 text-green-600">Low</th>
                  <th className="text-right px-3 py-2">Total</th>
                </tr>
              </thead>
              <tbody>
                {blocks?.blocks?.map(b => (
                  <tr key={b.block} className="border-t hover:bg-blue-50 cursor-pointer"
                    onClick={() => nav(`/block/${name}/${b.block}`)}>
                    <td className="px-3 py-2 font-medium">{b.block}</td>
                    <td className="px-2 py-2 text-center">{b.CRITICAL || 0}</td>
                    <td className="px-2 py-2 text-center">{b.HIGH || 0}</td>
                    <td className="px-2 py-2 text-center">{b.MODERATE || 0}</td>
                    <td className="px-2 py-2 text-center">{b.LOW || 0}</td>
                    <td className="px-3 py-2 text-right font-mono">{b.total}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Priority Schools + Proposal Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Priority Schools */}
        <div className="lg:col-span-2 card overflow-hidden">
          <h3 className="font-semibold mb-3">Priority Schools (Top 5% & 10%)</h3>
          <div className="overflow-x-auto max-h-80">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 sticky top-0">
                <tr>
                  <th className="text-left px-3 py-2">Rank</th>
                  <th className="text-left px-3 py-2">School</th>
                  <th className="text-left px-3 py-2">Block</th>
                  <th className="text-center px-3 py-2">Risk</th>
                  <th className="text-center px-3 py-2">Bucket</th>
                  <th className="text-right px-3 py-2">CR Gap</th>
                  <th className="text-right px-3 py-2">TR Gap</th>
                  <th className="text-center px-3 py-2">Chronic</th>
                </tr>
              </thead>
              <tbody>
                {priority?.schools?.map(s => (
                  <tr key={s.school_id} className="border-t hover:bg-blue-50 cursor-pointer"
                    onClick={() => nav(`/school/${s.school_id}`)}>
                    <td className="px-3 py-2 font-mono">{s.state_rank}</td>
                    <td className="px-3 py-2 truncate max-w-[200px]">{s.school_name || s.school_id}</td>
                    <td className="px-3 py-2">{s.block}</td>
                    <td className="px-3 py-2 text-center"><RiskBadge level={s.risk_level} /></td>
                    <td className="px-3 py-2 text-center text-xs font-mono">{s.priority_bucket}</td>
                    <td className="px-3 py-2 text-right">{s.classroom_gap}</td>
                    <td className="px-3 py-2 text-right">{s.teacher_gap}</td>
                    <td className="px-3 py-2 text-center">{s.persistent_high_risk_flag ? '⚠️' : ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Proposal Summary */}
        <div className="card">
          <h3 className="font-semibold mb-3">Proposal Validation</h3>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={proposalPie} dataKey="value" cx="50%" cy="50%" outerRadius={65}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                {proposalPie.map((e, i) => <Cell key={i} fill={DEC_COLORS[e.name] || '#999'} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          {proposals?.flagged?.length > 0 && (
            <>
              <h4 className="text-xs font-semibold text-gray-500 mt-3 mb-2">FLAGGED PROPOSALS</h4>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {proposals.flagged.slice(0, 5).map(f => (
                  <div key={f.school_id} className="text-xs flex justify-between cursor-pointer hover:text-blue-600"
                    onClick={() => nav(`/school/${f.school_id}`)}>
                    <span className="truncate">{f.school_name || f.school_id}</span>
                    <span className="text-yellow-600">{f.reason_code}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
