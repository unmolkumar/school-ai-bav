import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchSchoolOverview, fetchSchoolHistory, fetchSchoolForecast, fetchSchoolFacilities, fetchProposals } from '../api';
import { KPICard, RiskBadge, StatusBadge, TrendArrow, Loader } from '../components/Shared';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';

export default function SchoolDashboard() {
  const { id } = useParams();
  const [overview, setOverview] = useState(null);
  const [history, setHistory] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [facilities, setFacilities] = useState(null);
  const [proposals, setProposals] = useState(null);

  useEffect(() => {
    fetchSchoolOverview(id).then(setOverview);
    fetchSchoolHistory(id).then(setHistory);
    fetchSchoolForecast(id).then(setForecast);
    fetchSchoolFacilities(id).then(setFacilities);
    fetchProposals(id).then(setProposals);
  }, [id]);

  if (!overview) return <Loader />;

  const s = overview.school;
  const l = overview.latest;

  const gapData = [
    { name: 'Classrooms', actual: l.usable_class_rooms, required: l.required_class_rooms, gap: l.classroom_gap },
    { name: 'Teachers', actual: l.total_teachers, required: l.required_teachers, gap: l.teacher_gap },
  ];

  // Forecast chart data
  const forecastChart = [];
  if (history?.length) {
    history.forEach(h => forecastChart.push({
      year: h.academic_year, type: 'Historical', enrolment: h.total_enrolment,
    }));
  }
  if (forecast?.ml?.length) {
    forecast.ml.forEach(f => forecastChart.push({
      year: f.forecast_year, type: 'ML Forecast', enrolment: f.projected_enrolment,
    }));
  }

  const histEnrl = history?.map(h => ({
    year: h.academic_year,
    enrolment: h.total_enrolment,
    risk: h.risk_score,
  })) || [];

  const fcastBars = [];
  if (forecast?.wma?.length && forecast?.ml?.length) {
    forecast.wma.forEach((w, i) => {
      fcastBars.push({
        horizon: `T+${w.years_ahead}`,
        'WMA': w.projected_enrolment,
        'ML': forecast.ml[i]?.projected_enrolment || 0,
      });
    });
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        {s.district && <Link to={`/district/${s.district}`} className="text-blue-600 hover:underline text-sm">← {s.district}</Link>}
        <div>
          <h1 className="text-2xl font-bold">{s.school_name || id}</h1>
          <p className="text-sm text-gray-500">{s.district} · {s.block} · Category {s.school_category} · {s.management_type}</p>
        </div>
      </div>

      {/* Risk Card + KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        <div className="card col-span-2 flex items-center gap-4">
          <div className="relative w-20 h-20">
            <svg viewBox="0 0 36 36" className="w-20 h-20 -rotate-90">
              <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none" stroke="#e5e7eb" strokeWidth="3" />
              <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke={l.risk_score >= 0.6 ? '#ef4444' : l.risk_score >= 0.4 ? '#f97316' : l.risk_score >= 0.2 ? '#eab308' : '#22c55e'}
                strokeWidth="3"
                strokeDasharray={`${(l.risk_score || 0) * 100}, 100`} />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center text-lg font-bold">
              {l.risk_score?.toFixed(2)}
            </div>
          </div>
          <div>
            <RiskBadge level={l.risk_level} />
            <div className="mt-1 text-sm"><TrendArrow delta={l.risk_delta} /> <span className="text-gray-500">{l.trend_direction}</span></div>
            {l.is_chronic ? <p className="text-xs text-red-600 mt-1">⚠ Chronic high-risk (3+ years)</p> : null}
            {l.persistent_high_risk ? <p className="text-xs text-orange-600">Persistent high-risk</p> : null}
          </div>
        </div>
        <KPICard label="Enrolment" value={l.total_enrolment} color="blue" />
        <KPICard label="Classroom Gap" value={l.classroom_gap} color="orange" />
        <KPICard label="Teacher Gap" value={l.teacher_gap} color="purple" />
        <KPICard label="Priority" value={l.priority_bucket} sub={`Rank #${l.risk_rank}`} color="yellow" />
      </div>

      {/* Gap Analysis + History */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Gap Bars */}
        <div className="card">
          <h3 className="font-semibold mb-3">Gap Analysis</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={gapData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" tick={{ fontSize: 10 }} />
              <YAxis dataKey="name" type="category" tick={{ fontSize: 12 }} width={80} />
              <Tooltip />
              <Bar dataKey="actual" fill="#22c55e" name="Available" />
              <Bar dataKey="required" fill="#6366f1" name="Required" />
              <Legend />
            </BarChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-2 gap-4 mt-3 text-sm">
            <div>
              <p className="text-gray-500">Classrooms</p>
              <p>{l.usable_class_rooms} available / {l.required_class_rooms} required</p>
              <p className="text-red-600 font-medium">Gap: {l.classroom_gap}</p>
            </div>
            <div>
              <p className="text-gray-500">Teachers</p>
              <p>{l.total_teachers} available / {l.required_teachers} required</p>
              <p className="text-red-600 font-medium">Gap: {l.teacher_gap}</p>
            </div>
          </div>
        </div>

        {/* Enrolment History */}
        <div className="card">
          <h3 className="font-semibold mb-3">Enrolment History (7yr)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={histEnrl}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Line type="monotone" dataKey="enrolment" stroke="#3b82f6" strokeWidth={2} name="Enrolment" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Forecast + Facilities */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Forecast */}
        <div className="card">
          <h3 className="font-semibold mb-3">Enrolment Forecast</h3>
          {fcastBars.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={fcastBars}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="horizon" />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Bar dataKey="WMA" fill="#d1d5db" name="Phase 10 (WMA)" />
                  <Bar dataKey="ML" fill="#8b5cf6" name="Phase 11 (ML)" />
                  <Legend />
                </BarChart>
              </ResponsiveContainer>
              <div className="mt-3 text-xs space-y-1">
                {forecast.ml.map(f => (
                  <div key={f.years_ahead} className="flex justify-between">
                    <span>{f.forecast_year}</span>
                    <span>Enrl: {f.projected_enrolment?.toLocaleString()} | CR gap: {f.projected_classroom_gap} | TR gap: {f.projected_teacher_gap}</span>
                  </div>
                ))}
              </div>
            </>
          ) : <p className="text-sm text-gray-500">No forecast data available.</p>}
        </div>

        {/* Facility Checklist */}
        <div className="card">
          <h3 className="font-semibold mb-3">Facility Checklist</h3>
          {facilities ? (
            <div className="grid grid-cols-2 gap-3">
              {[
                ['Drinking Water', facilities.drinking_water],
                ['Electricity', facilities.electricity],
                ['Internet', facilities.internet],
                ['Girls Toilet', facilities.girls_toilet],
                ['Ramp (Accessibility)', facilities.ramp],
                ['CWSN Toilet', facilities.cwsn_toilet],
                ['Resource Room', facilities.resource_room],
              ].map(([name, val]) => (
                <div key={name} className="flex items-center gap-2 text-sm">
                  <span className={`text-lg ${val ? 'text-green-500' : 'text-red-400'}`}>{val ? '✓' : '✗'}</span>
                  <span>{name}</span>
                </div>
              ))}
              <div className="col-span-2 mt-2 pt-2 border-t text-sm space-y-1">
                <p>Building: <span className="font-medium">{facilities.building_condition || 'N/A'}</span></p>
                <p>Classroom Score: <span className="font-medium">{facilities.classroom_condition_score ?? 'N/A'}</span></p>
                <p>Total / Usable Rooms: {facilities.total_class_rooms} / {facilities.usable_class_rooms}</p>
              </div>
            </div>
          ) : <p className="text-sm text-gray-500">No facility data.</p>}
        </div>
      </div>

      {/* Proposal History */}
      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold">Proposal History</h3>
          <Link to={`/proposals?school=${id}`} className="text-sm text-blue-600 hover:underline">+ Submit New Proposal</Link>
        </div>
        {proposals?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-3 py-2">Year</th>
                  <th className="text-right px-3 py-2">CR Req</th>
                  <th className="text-right px-3 py-2">TR Req</th>
                  <th className="text-center px-3 py-2">Status</th>
                  <th className="text-left px-3 py-2">Reason</th>
                  <th className="text-right px-3 py-2">Confidence</th>
                  <th className="text-left px-3 py-2">Submitted</th>
                </tr>
              </thead>
              <tbody>
                {proposals.map(p => (
                  <tr key={p.id} className="border-t">
                    <td className="px-3 py-2">{p.academic_year}</td>
                    <td className="px-3 py-2 text-right">{p.classrooms_requested}</td>
                    <td className="px-3 py-2 text-right">{p.teachers_requested}</td>
                    <td className="px-3 py-2 text-center"><StatusBadge status={p.decision_status} /></td>
                    <td className="px-3 py-2 text-xs">{p.reason_code}</td>
                    <td className="px-3 py-2 text-right">{p.confidence_score?.toFixed(2)}</td>
                    <td className="px-3 py-2 text-xs text-gray-500">{p.submitted_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <p className="text-sm text-gray-500">No proposals submitted yet.</p>}
      </div>
    </div>
  );
}
