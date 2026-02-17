import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { submitProposal, searchSchools, fetchSchoolOverview, fetchStateYears } from '../api';
import { KPICard, StatusBadge, Loader } from '../components/Shared';
import { FileText, Search, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

export default function ProposalSubmission() {
  const [searchParams] = useSearchParams();
  const prefillId = searchParams.get('school') || '';

  const [years, setYears] = useState([]);
  const [form, setForm] = useState({
    school_id: prefillId,
    academic_year: '',
    classrooms_requested: 0,
    teachers_requested: 0,
    justification: '',
    submitted_by: '',
  });
  const [schoolSearch, setSchoolSearch] = useState(prefillId);
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [schoolInfo, setSchoolInfo] = useState(null);
  const [loadingInfo, setLoadingInfo] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  // Load years
  useEffect(() => {
    fetchStateYears().then(y => {
      setYears(y);
      if (y.length) setForm(f => ({ ...f, academic_year: f.academic_year || y[y.length - 1] }));
    }).catch(() => {});
  }, []);

  // Load school info if prefilled
  useEffect(() => {
    if (prefillId) {
      setLoadingInfo(true);
      fetchSchoolOverview(prefillId).then(setSchoolInfo).catch(() => {}).finally(() => setLoadingInfo(false));
    }
  }, [prefillId]);

  // Debounced search
  const doSearch = useCallback((q) => {
    if (q.length < 3) { setSearchResults([]); return; }
    setSearching(true);
    searchSchools(q).then(setSearchResults).catch(() => setSearchResults([])).finally(() => setSearching(false));
  }, []);

  useEffect(() => {
    const t = setTimeout(() => doSearch(schoolSearch), 300);
    return () => clearTimeout(t);
  }, [schoolSearch, doSearch]);

  const selectSchool = (s) => {
    setForm(f => ({ ...f, school_id: s.school_id }));
    setSchoolSearch(s.school_id);
    setSearchResults([]);
    setLoadingInfo(true);
    fetchSchoolOverview(s.school_id).then(setSchoolInfo).catch(() => {}).finally(() => setLoadingInfo(false));
  };

  const handleChange = (field, value) => {
    setForm(f => ({ ...f, [field]: value }));
    setResult(null);
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.school_id) { setError('Please select a school.'); return; }
    if (!form.academic_year) { setError('Please select an academic year.'); return; }
    if (form.classrooms_requested === 0 && form.teachers_requested === 0) {
      setError('Request at least 1 classroom or 1 teacher.');
      return;
    }
    setSubmitting(true);
    setError('');
    setResult(null);
    try {
      const res = await submitProposal(form);
      setResult(res);
    } catch (err) {
      setError(err.message || 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  const statusIcon = {
    ACCEPTED: <CheckCircle className="w-6 h-6 text-green-600" />,
    FLAGGED: <AlertTriangle className="w-6 h-6 text-yellow-600" />,
    REJECTED: <XCircle className="w-6 h-6 text-red-600" />,
  };

  const statusBg = {
    ACCEPTED: 'bg-green-50 border-green-300',
    FLAGGED: 'bg-yellow-50 border-yellow-300',
    REJECTED: 'bg-red-50 border-red-300',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <FileText className="w-6 h-6 text-blue-600" />
        <h1 className="text-2xl font-bold">Submit School Proposal</h1>
      </div>
      <p className="text-gray-500 text-sm">
        Submit a resource request for a school. The system validates it instantly against actual infrastructure
        and teacher gaps, returning ACCEPTED / FLAGGED / REJECTED with a confidence score.
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ── Form ────────────────────────────── */}
        <form onSubmit={handleSubmit} className="lg:col-span-2 card space-y-5">
          {/* School Search */}
          <div className="relative">
            <label className="block text-sm font-medium text-gray-700 mb-1">School ID / Name</label>
            <div className="relative">
              <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={schoolSearch}
                onChange={e => { setSchoolSearch(e.target.value); handleChange('school_id', ''); setSchoolInfo(null); }}
                placeholder="Search by UDISE code or school name…"
                className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-400 focus:outline-none"
              />
            </div>
            {searching && <p className="text-xs text-gray-400 mt-1">Searching…</p>}
            {searchResults.length > 0 && (
              <ul className="absolute z-30 w-full bg-white border rounded-lg shadow-lg mt-1 max-h-48 overflow-y-auto">
                {searchResults.map(s => (
                  <li key={s.school_id}
                    className="px-4 py-2 text-sm hover:bg-blue-50 cursor-pointer flex justify-between"
                    onClick={() => selectSchool(s)}>
                    <span className="font-medium">{s.school_id}</span>
                    <span className="text-gray-500 truncate ml-2">{s.district} › {s.block}</span>
                  </li>
                ))}
              </ul>
            )}
            {form.school_id && (
              <p className="text-xs text-green-600 mt-1">✓ Selected: {form.school_id}</p>
            )}
          </div>

          {/* Year */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Academic Year</label>
            <select value={form.academic_year} onChange={e => handleChange('academic_year', e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-400 focus:outline-none">
              {years.map(y => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>

          {/* Numeric inputs */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Classrooms Requested</label>
              <input type="number" min={0} max={100} value={form.classrooms_requested}
                onChange={e => handleChange('classrooms_requested', parseInt(e.target.value) || 0)}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-400 focus:outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Teachers Requested</label>
              <input type="number" min={0} max={100} value={form.teachers_requested}
                onChange={e => handleChange('teachers_requested', parseInt(e.target.value) || 0)}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-400 focus:outline-none" />
            </div>
          </div>

          {/* Justification */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Justification (optional)</label>
            <textarea value={form.justification} rows={3}
              onChange={e => handleChange('justification', e.target.value)}
              placeholder="Brief reason for the request…"
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-400 focus:outline-none resize-none" />
          </div>

          {/* Submitted By */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Submitted By</label>
            <input type="text" value={form.submitted_by}
              onChange={e => handleChange('submitted_by', e.target.value)}
              placeholder="Your name / role"
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-400 focus:outline-none" />
          </div>

          {error && <p className="text-sm text-red-600 bg-red-50 rounded px-3 py-2">{error}</p>}

          <button type="submit" disabled={submitting}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2.5 rounded-lg transition disabled:opacity-50">
            {submitting ? 'Validating…' : 'Submit Proposal'}
          </button>
        </form>

        {/* ── Context Panel ───────────────────── */}
        <div className="space-y-4">
          {loadingInfo && <Loader />}
          {schoolInfo && (
            <>
              <div className="card">
                <h3 className="font-semibold text-sm mb-3 text-gray-700">School Context</h3>
                <dl className="space-y-2 text-sm">
                  <div className="flex justify-between"><dt className="text-gray-500">District</dt><dd>{schoolInfo.district}</dd></div>
                  <div className="flex justify-between"><dt className="text-gray-500">Block</dt><dd>{schoolInfo.block}</dd></div>
                  <div className="flex justify-between"><dt className="text-gray-500">Category</dt><dd>{schoolInfo.category}</dd></div>
                  <div className="flex justify-between"><dt className="text-gray-500">Risk</dt><dd><StatusBadge status={schoolInfo.risk_level} /></dd></div>
                  <div className="flex justify-between"><dt className="text-gray-500">Priority Rank</dt><dd>#{schoolInfo.risk_rank?.toLocaleString()}</dd></div>
                </dl>
              </div>
              <div className="card">
                <h3 className="font-semibold text-sm mb-3 text-gray-700">Current Gaps</h3>
                <div className="grid grid-cols-2 gap-3">
                  <KPICard label="Classroom Gap" value={schoolInfo.classroom_gap ?? 0} color={schoolInfo.classroom_gap > 0 ? 'red' : 'green'} />
                  <KPICard label="Teacher Gap" value={schoolInfo.teacher_gap ?? 0} color={schoolInfo.teacher_gap > 0 ? 'red' : 'green'} />
                </div>
                <p className="text-xs text-gray-400 mt-2">
                  Use these gaps as a guide for your request amounts.
                </p>
              </div>
            </>
          )}
          {!schoolInfo && !loadingInfo && (
            <div className="card text-sm text-gray-400 text-center py-8">
              Search and select a school to see context
            </div>
          )}
        </div>
      </div>

      {/* ── Result Panel ──────────────────────── */}
      {result && (
        <div className={`card border-2 ${statusBg[result.decision_status] || 'border-gray-200'}`}>
          <div className="flex items-center gap-3 mb-4">
            {statusIcon[result.decision_status]}
            <div>
              <h3 className="font-bold text-lg">{result.decision_status}</h3>
              <p className="text-sm text-gray-600">{result.message}</p>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KPICard label="Confidence" value={`${(result.confidence_score * 100).toFixed(0)}%`}
              color={result.confidence_score >= 0.7 ? 'green' : result.confidence_score >= 0.4 ? 'yellow' : 'red'} />
            <KPICard label="Reason" value={result.reason_code?.replace(/_/g, ' ')} color="purple" />
            <KPICard label="Classroom Ratio"
              value={result.classroom_ratio != null ? result.classroom_ratio.toFixed(2) : '—'}
              sub="requested/gap" color="blue" />
            <KPICard label="Teacher Ratio"
              value={result.teacher_ratio != null ? result.teacher_ratio.toFixed(2) : '—'}
              sub="requested/gap" color="blue" />
          </div>
          {result.actual_gaps && (
            <div className="mt-4 bg-white bg-opacity-50 rounded-lg p-3 text-sm">
              <p className="text-gray-500">
                Actual classroom gap: <strong>{result.actual_gaps.classroom_gap ?? 0}</strong> |
                Teacher gap: <strong>{result.actual_gaps.teacher_gap ?? 0}</strong> |
                Enrolment: <strong>{result.actual_gaps.total_enrolment?.toLocaleString() ?? '—'}</strong>
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
