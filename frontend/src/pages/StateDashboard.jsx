import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchStateOverview, fetchStateTrends, fetchStateBudget, fetchStateForecast, fetchStateYears } from '../api';
import { KPICard, GradeBadge, TrendArrow, Loader } from '../components/Shared';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, PieChart, Pie, Cell, Legend } from 'recharts';

const RISK_COLORS = { CRITICAL: '#ef4444', HIGH: '#f97316', MODERATE: '#eab308', LOW: '#22c55e' };
const PIE_COLORS = ['#22c55e', '#eab308', '#ef4444'];

export default function StateDashboard() {
  const [data, setData] = useState(null);
  const [trends, setTrends] = useState(null);
  const [budget, setBudget] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [years, setYears] = useState([]);
  const [year, setYear] = useState('');
  const nav = useNavigate();

  useEffect(() => {
    fetchStateYears().then(y => { setYears(y); setYear(y[y.length - 1]); });
    fetchStateTrends().then(setTrends);
    fetchStateForecast().then(setForecast);
  }, []);

  useEffect(() => {
    if (year) {
      fetchStateOverview(year).then(setData);
      fetchStateBudget(year).then(setBudget);
    }
  }, [year]);

  if (!data) return <Loader />;

  const k = data.kpis;
  const budgetPie = budget?.by_status?.map(s => ({ name: s.allocation_status, value: s.count })) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">State Dashboard</h1>
          <p className="text-sm text-gray-500">Commissioner / Secretary — Andhra Pradesh</p>
        </div>
        <select value={year} onChange={e => setYear(e.target.value)}
          className="border rounded-lg px-3 py-1.5 text-sm">
          {years.map(y => <option key={y} value={y}>{y}</option>)}
        </select>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KPICard label="Total Schools" value={k.total_schools} color="blue" />
        <KPICard label="Critical" value={k.critical_schools} sub={`${(k.critical_schools / k.total_schools * 100).toFixed(1)}%`} color="red" />
        <KPICard label="Classroom Gap" value={k.total_classroom_gap} color="orange" />
        <KPICard label="Teacher Gap" value={k.total_teacher_gap} color="purple" />
      </div>

      {/* District Compliance Table + Risk Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* District Table */}
        <div className="lg:col-span-2 card overflow-hidden">
          <h3 className="font-semibold mb-3">District Compliance Index</h3>
          <div className="overflow-x-auto max-h-96">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 sticky top-0">
                <tr>
                  <th className="text-left px-3 py-2">Rank</th>
                  <th className="text-left px-3 py-2">District</th>
                  <th className="text-center px-3 py-2">Grade</th>
                  <th className="text-right px-3 py-2">Avg Risk</th>
                  <th className="text-right px-3 py-2">YoY</th>
                  <th className="text-right px-3 py-2">Critical %</th>
                  <th className="text-right px-3 py-2">Schools</th>
                </tr>
              </thead>
              <tbody>
                {data.districts.map(d => (
                  <tr key={d.district} className="border-t hover:bg-blue-50 cursor-pointer"
                    onClick={() => nav(`/district/${d.district}`)}>
                    <td className="px-3 py-2 font-mono">{d.district_rank}</td>
                    <td className="px-3 py-2 font-medium">{d.district}</td>
                    <td className="px-3 py-2 text-center"><GradeBadge grade={d.compliance_grade} /></td>
                    <td className="px-3 py-2 text-right">{d.avg_risk_score?.toFixed(3)}</td>
                    <td className="px-3 py-2 text-right"><TrendArrow delta={d.yoy_risk_improvement} /></td>
                    <td className="px-3 py-2 text-right">{d.pct_high_critical?.toFixed(1)}%</td>
                    <td className="px-3 py-2 text-right">{d.total_schools?.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Risk Trend */}
        <div className="card">
          <h3 className="font-semibold mb-3">State Risk Trend (7yr)</h3>
          {trends && (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={trends.risk_trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="academic_year" tick={{ fontSize: 10 }} />
                <YAxis domain={[0, 0.5]} tick={{ fontSize: 10 }} />
                <Tooltip />
                <Line type="monotone" dataKey="avg_risk" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          )}
          <h3 className="font-semibold mt-5 mb-3">Enrolment Trend</h3>
          {trends && (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={trends.enrolment_trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="academic_year" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} tickFormatter={v => `${(v / 1e6).toFixed(1)}M`} />
                <Tooltip formatter={v => v.toLocaleString()} />
                <Bar dataKey="total_enrolment" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Budget + Forecast Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Budget Summary */}
        <div className="card">
          <h3 className="font-semibold mb-3">Budget Allocation ({year})</h3>
          <div className="flex items-center gap-6">
            <ResponsiveContainer width={180} height={180}>
              <PieChart>
                <Pie data={budgetPie} dataKey="value" cx="50%" cy="50%" outerRadius={70} label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}>
                  {budgetPie.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-2 text-sm">
              {budget?.by_status?.map(s => (
                <div key={s.allocation_status} className="flex justify-between gap-4">
                  <span>{s.allocation_status}</span>
                  <span className="font-mono">{s.count?.toLocaleString()}</span>
                </div>
              ))}
              <div className="pt-2 border-t text-xs text-gray-500">
                Classrooms: {budget?.by_status?.reduce((a, s) => a + (s.classrooms || 0), 0)?.toLocaleString()} | Teachers: {budget?.by_status?.reduce((a, s) => a + (s.teachers || 0), 0)?.toLocaleString()}
              </div>
            </div>
          </div>
        </div>

        {/* Forecast */}
        <div className="card">
          <h3 className="font-semibold mb-3">Forecast — Projected Gaps</h3>
          {forecast && (
            <>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={forecast.ml.map((m, i) => ({
                  horizon: `T+${m.years_ahead} (${m.forecast_year})`,
                  'ML cr_gap': m.cr_gap,
                  'WMA cr_gap': forecast.wma[i]?.cr_gap || 0,
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="horizon" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} tickFormatter={v => `${(v / 1000).toFixed(0)}k`} />
                  <Tooltip formatter={v => v.toLocaleString()} />
                  <Bar dataKey="ML cr_gap" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="WMA cr_gap" fill="#d1d5db" radius={[4, 4, 0, 0]} />
                  <Legend />
                </BarChart>
              </ResponsiveContainer>
              <p className="text-xs text-gray-500 mt-2">
                ML mean growth: {forecast.ml[0]?.mean_growth} | WMA mean growth: {forecast.wma[0]?.mean_growth}
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
