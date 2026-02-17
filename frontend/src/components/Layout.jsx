import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useState, useRef } from 'react';
import { BarChart3, Building2, MapPin, School, FileText, Wallet, Search } from 'lucide-react';
import { searchSchools } from '../api';

const NAV = [
  { to: '/state',     icon: BarChart3, label: 'State' },
  { to: '/proposals', icon: FileText,  label: 'Proposals' },
  { to: '/budget',    icon: Wallet,    label: 'Budget Sim' },
];

export default function Layout() {
  const loc = useLocation();
  const nav = useNavigate();
  const [q, setQ] = useState('');
  const [results, setResults] = useState([]);
  const [showSearch, setShowSearch] = useState(false);
  const timer = useRef(null);

  const handleSearch = (val) => {
    setQ(val);
    clearTimeout(timer.current);
    if (val.length < 2) { setResults([]); return; }
    timer.current = setTimeout(async () => {
      try {
        const r = await searchSchools(val);
        setResults(r);
        setShowSearch(true);
      } catch { setResults([]); }
    }, 300);
  };

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-56 bg-slate-900 text-white flex flex-col flex-shrink-0">
        <div className="p-4 border-b border-slate-700">
          <h1 className="text-lg font-bold tracking-tight">School AI BAV</h1>
          <p className="text-xs text-slate-400 mt-0.5">Andhra Pradesh</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {NAV.map(({ to, icon: Icon, label }) => (
            <Link key={to} to={to}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition
                ${loc.pathname === to ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800'}`}>
              <Icon size={16} /> {label}
            </Link>
          ))}
        </nav>
        <div className="p-3 border-t border-slate-700 text-xs text-slate-500">
          v1.0 · 12 tables · 67k schools
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="h-14 bg-white border-b border-gray-200 flex items-center px-5 gap-4 flex-shrink-0">
          <div className="relative flex-1 max-w-md">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search schools by name or ID…"
              className="w-full pl-9 pr-3 py-1.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={q}
              onChange={e => handleSearch(e.target.value)}
              onFocus={() => results.length && setShowSearch(true)}
              onBlur={() => setTimeout(() => setShowSearch(false), 200)}
            />
            {showSearch && results.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-white rounded-lg shadow-lg border max-h-64 overflow-y-auto z-50">
                {results.map(s => (
                  <button key={s.school_id}
                    className="w-full text-left px-4 py-2 hover:bg-gray-50 text-sm border-b last:border-0"
                    onMouseDown={() => { nav(`/school/${s.school_id}`); setQ(''); setShowSearch(false); }}>
                    <div className="font-medium truncate">{s.school_name || s.school_id}</div>
                    <div className="text-xs text-gray-500">{s.district} · {s.block} · Cat {s.school_category}</div>
                  </button>
                ))}
              </div>
            )}
          </div>
          <span className="text-xs text-gray-400">
            {loc.pathname.replace(/\//g, ' › ').slice(3) || 'Dashboard'}
          </span>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-auto p-5">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
