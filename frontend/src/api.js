const BASE = '/api';

async function get(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// ── State ─────────────────────────────────────────
export const fetchStateOverview   = (year) => get(`/state/overview${year ? `?year=${year}` : ''}`);
export const fetchStateYears      = ()     => get('/state/years');
export const fetchStateTrends     = ()     => get('/state/trends');
export const fetchStateBudget     = (year) => get(`/state/budget${year ? `?year=${year}` : ''}`);
export const fetchStateForecast   = ()     => get('/state/forecast');

// ── District ──────────────────────────────────────
export const fetchDistrictList       = ()   => get('/district/list');
export const fetchDistrictCompliance = (d)  => get(`/district/${encodeURIComponent(d)}/compliance`);
export const fetchDistrictBlocks     = (d, y) => get(`/district/${encodeURIComponent(d)}/blocks${y ? `?year=${y}` : ''}`);
export const fetchDistrictPriority   = (d, y) => get(`/district/${encodeURIComponent(d)}/priority${y ? `?year=${y}` : ''}`);
export const fetchDistrictProposals  = (d, y) => get(`/district/${encodeURIComponent(d)}/proposals${y ? `?year=${y}` : ''}`);
export const fetchDistrictTrend      = (d)  => get(`/district/${encodeURIComponent(d)}/trend`);

// ── Block ─────────────────────────────────────────
export const fetchBlockSummary  = (d, b, y) => get(`/school/block/${encodeURIComponent(d)}/${encodeURIComponent(b)}/summary${y ? `?year=${y}` : ''}`);
export const fetchBlockSchools  = (d, b, y) => get(`/school/block/${encodeURIComponent(d)}/${encodeURIComponent(b)}/schools${y ? `?year=${y}` : ''}`);
export const fetchBlockChronic  = (d, b, y) => get(`/school/block/${encodeURIComponent(d)}/${encodeURIComponent(b)}/chronic${y ? `?year=${y}` : ''}`);

// ── School ────────────────────────────────────────
export const fetchSchoolOverview    = (id) => get(`/school/${id}/overview`);
export const fetchSchoolHistory     = (id) => get(`/school/${id}/history`);
export const fetchSchoolForecast    = (id) => get(`/school/${id}/forecast`);
export const fetchSchoolFacilities  = (id) => get(`/school/${id}/facilities`);
export const searchSchools          = (q)  => get(`/school/search?q=${encodeURIComponent(q)}`);

// ── Proposals ─────────────────────────────────────
export const submitProposal     = (data)  => post('/proposals/submit', data);
export const fetchProposals     = (id)    => get(`/proposals/school/${id}`);
export const simulateBudget     = (params) => post('/proposals/budget/simulate', params);
