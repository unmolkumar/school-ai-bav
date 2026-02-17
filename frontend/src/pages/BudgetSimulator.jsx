import { useState } from 'react';
import { simulateBudget } from '../api';
import { KPICard, Loader } from '../components/Shared';
import { Wallet, Play, TrendingUp } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';

const COLORS = ['#22c55e', '#eab308', '#ef4444'];

export default function BudgetSimulator() {
  const [params, setParams] = useState({
    total_budget_cr: 50,
    cost_per_classroom_lakh: 5,
    max_teachers: 10000,
    year: '',
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleChange = (field, value) => {
    setParams(p => ({ ...p, [field]: value }));
    setError('');
  };

  const runSimulation = async () => {
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const body = { ...params };
      if (!body.year) delete body.year; // let backend pick latest
      const res = await simulateBudget(body);
      setResult(res);
    } catch (err) {
      setError(err.message || 'Simulation failed');
    } finally {
      setLoading(false);
    }
  };

  const summary = result?.summary;
  const pieData = summary ? [
    { name: 'Funded', value: summary.funded },
    { name: 'Partial', value: summary.partially_funded },
    { name: 'Unfunded', value: summary.unfunded },
  ] : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Wallet className="w-6 h-6 text-purple-600" />
        <h1 className="text-2xl font-bold">Budget Simulator</h1>
      </div>
      <p className="text-gray-500 text-sm">
        Adjust budget parameters and run a simulation to see how resources would be allocated across
        schools, ranked by priority index. Results are non-destructive — they don't modify any data.
      </p>

      {/* ── Parameter Controls ─────────────── */}
      <div className="card">
        <h2 className="font-semibold mb-4 text-gray-700 flex items-center gap-2">
          <TrendingUp className="w-4 h-4" /> Simulation Parameters
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Total Budget (₹ Cr)
            </label>
            <input type="number" min={1} max={500} step={1}
              value={params.total_budget_cr}
              onChange={e => handleChange('total_budget_cr', parseFloat(e.target.value) || 50)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-purple-400 focus:outline-none" />
            <input type="range" min={1} max={500} step={1}
              value={params.total_budget_cr}
              onChange={e => handleChange('total_budget_cr', parseFloat(e.target.value))}
              className="w-full mt-1 accent-purple-600" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Cost per Classroom (₹ Lakh)
            </label>
            <input type="number" min={1} max={50} step={0.5}
              value={params.cost_per_classroom_lakh}
              onChange={e => handleChange('cost_per_classroom_lakh', parseFloat(e.target.value) || 5)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-purple-400 focus:outline-none" />
            <input type="range" min={1} max={50} step={0.5}
              value={params.cost_per_classroom_lakh}
              onChange={e => handleChange('cost_per_classroom_lakh', parseFloat(e.target.value))}
              className="w-full mt-1 accent-purple-600" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Max Teacher Postings
            </label>
            <input type="number" min={100} max={100000} step={100}
              value={params.max_teachers}
              onChange={e => handleChange('max_teachers', parseInt(e.target.value) || 10000)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-purple-400 focus:outline-none" />
            <input type="range" min={100} max={100000} step={100}
              value={params.max_teachers}
              onChange={e => handleChange('max_teachers', parseInt(e.target.value))}
              className="w-full mt-1 accent-purple-600" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Academic Year (blank = latest)
            </label>
            <input type="text" value={params.year} placeholder="e.g. 2024-25"
              onChange={e => handleChange('year', e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-purple-400 focus:outline-none" />
          </div>
        </div>

        <button onClick={runSimulation} disabled={loading}
          className="mt-5 flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white font-semibold px-6 py-2.5 rounded-lg transition disabled:opacity-50">
          <Play className="w-4 h-4" />
          {loading ? 'Running…' : 'Run Simulation'}
        </button>
      </div>

      {error && <p className="text-sm text-red-600 bg-red-50 rounded px-3 py-2">{error}</p>}
      {loading && <Loader />}

      {/* ── Results ────────────────────────── */}
      {result && (
        <>
          {/* KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KPICard label="Fully Funded" value={summary.funded.toLocaleString()} color="green" sub={`of ${summary.total_schools.toLocaleString()}`} />
            <KPICard label="Partially Funded" value={summary.partially_funded.toLocaleString()} color="yellow" />
            <KPICard label="Unfunded" value={summary.unfunded.toLocaleString()} color="red" />
            <KPICard label="Budget Used" value={`${summary.budget_utilisation_pct}%`} color="purple"
              sub={`₹${summary.total_cost_cr} Cr of ₹${result.params.total_budget_cr} Cr`} />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KPICard label="Classrooms Allocated" value={summary.classrooms_allocated.toLocaleString()} color="blue"
              sub={`max possible ${result.params.max_classrooms.toLocaleString()}`} />
            <KPICard label="Teachers Allocated" value={summary.teachers_allocated.toLocaleString()} color="blue"
              sub={`cap ${result.params.max_teachers.toLocaleString()}`} />
            <KPICard label="Coverage" value={`${((summary.funded + summary.partially_funded) / summary.total_schools * 100).toFixed(1)}%`} color="green"
              sub="schools receiving resources" />
            <KPICard label="Year" value={result.params.year} color="purple" />
          </div>

          {/* Pie + Bar row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Funding Pie */}
            <div className="card">
              <h3 className="font-semibold text-sm mb-3 text-gray-700">Funding Distribution</h3>
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" outerRadius={100} dataKey="value" labelLine={false}
                    label={({ name, value, percent }) => `${name}: ${value.toLocaleString()} (${(percent * 100).toFixed(0)}%)`}>
                    {pieData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
                  </Pie>
                  <Legend />
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* District allocation bar */}
            <div className="card">
              <h3 className="font-semibold text-sm mb-3 text-gray-700">Top Districts — Classrooms Allocated</h3>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={result.by_district} layout="vertical" margin={{ left: 80 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis type="category" dataKey="district" tick={{ fontSize: 11 }} width={80} />
                  <Tooltip formatter={v => v.toLocaleString()} />
                  <Bar dataKey="classrooms" fill="#6366f1" name="Classrooms" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* District table */}
          <div className="card">
            <h3 className="font-semibold text-sm mb-3 text-gray-700">District Allocation Detail</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-gray-500 text-xs uppercase">
                    <th className="py-2 pr-4">District</th>
                    <th className="py-2 pr-4 text-right">Classrooms</th>
                    <th className="py-2 pr-4 text-right">Teachers</th>
                    <th className="py-2 pr-4 text-right">Cost (₹ Cr)</th>
                    <th className="py-2 text-right">Schools Served</th>
                  </tr>
                </thead>
                <tbody>
                  {result.by_district.map(d => (
                    <tr key={d.district} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-2 pr-4 font-medium">{d.district}</td>
                      <td className="py-2 pr-4 text-right">{d.classrooms.toLocaleString()}</td>
                      <td className="py-2 pr-4 text-right">{d.teachers.toLocaleString()}</td>
                      <td className="py-2 pr-4 text-right">{(d.cost / 10000000).toFixed(2)}</td>
                      <td className="py-2 text-right">{d.schools_served.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
