import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import StateDashboard from './pages/StateDashboard';
import DistrictDashboard from './pages/DistrictDashboard';
import BlockDashboard from './pages/BlockDashboard';
import SchoolDashboard from './pages/SchoolDashboard';
import ProposalSubmission from './pages/ProposalSubmission';
import BudgetSimulator from './pages/BudgetSimulator';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/state" replace />} />
          <Route path="/state" element={<StateDashboard />} />
          <Route path="/district/:name" element={<DistrictDashboard />} />
          <Route path="/block/:district/:block" element={<BlockDashboard />} />
          <Route path="/school/:id" element={<SchoolDashboard />} />
          <Route path="/proposals" element={<ProposalSubmission />} />
          <Route path="/budget" element={<BudgetSimulator />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
