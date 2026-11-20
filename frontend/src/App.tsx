import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout';
import { AgentsPage } from './pages/AgentsPage';
import { DashboardPage } from './pages/DashboardPage';
import { IntegrationsPage } from './pages/IntegrationsPage';
import { PlaygroundPage } from './pages/PlaygroundPage';
import { RunsPage } from './pages/RunsPage';
import { RunsProvider } from './state/runs';

export default function App() {
  return (
    <RunsProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<DashboardPage />} />
            <Route path="playground" element={<PlaygroundPage />} />
            <Route path="agents" element={<AgentsPage />} />
            <Route path="runs" element={<RunsPage />} />
            <Route path="integrations" element={<IntegrationsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </RunsProvider>
  );
}
