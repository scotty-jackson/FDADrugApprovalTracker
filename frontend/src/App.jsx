/**
 * Main App component with routing and layout
 */
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import RecentApprovals from './pages/RecentApprovals';
import UpcomingEvents from './pages/UpcomingEvents';
import DrugDetail from './pages/DrugDetail';
import MySubscriptions from './pages/MySubscriptions';
import About from './pages/About';
import TrialsExplorer from './pages/TrialsExplorer';
import TrialDetail from './pages/TrialDetail';
import CatalystCalendar from './pages/CatalystCalendar';
import CompanyDashboard from './pages/CompanyDashboard';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/approvals" element={<RecentApprovals />} />
        <Route path="/events" element={<UpcomingEvents />} />
        <Route path="/drugs/:id" element={<DrugDetail />} />
        <Route path="/subscriptions" element={<MySubscriptions />} />
        <Route path="/trials" element={<TrialsExplorer />} />
        <Route path="/trials/:id" element={<TrialDetail />} />
        <Route path="/catalysts" element={<CatalystCalendar />} />
        <Route path="/companies/:id" element={<CompanyDashboard />} />
        <Route path="/about" element={<About />} />
      </Routes>
    </Layout>
  );
}

export default App;
