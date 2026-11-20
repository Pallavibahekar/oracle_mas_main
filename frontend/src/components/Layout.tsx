import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { AGENTS } from '../data/agents';

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: '◫', end: true },
  { to: '/playground', label: 'Playground', icon: '⌘', end: false },
  { to: '/agents', label: 'Agents', icon: '⬡', end: false },
  { to: '/runs', label: 'Run history', icon: '≡', end: false },
  { to: '/integrations', label: 'Integrations', icon: '⊕', end: false },
];

const PAGE_META: Record<string, { title: string; subtitle: string }> = {
  '/': {
    title: 'Dashboard',
    subtitle: 'Live overview of the multi-agent system and its recent work.',
  },
  '/playground': {
    title: 'Playground',
    subtitle: 'Send a request and watch the router delegate it in real time.',
  },
  '/agents': {
    title: 'Agents',
    subtitle: 'The specialists behind every orchestrated response.',
  },
  '/runs': {
    title: 'Run history',
    subtitle: 'Every orchestration with its route, steps and final answer.',
  },
  '/integrations': {
    title: 'Integrations',
    subtitle: 'Tools and infrastructure the Python backend connects to.',
  },
};

export function Layout() {
  const { pathname } = useLocation();
  const meta = PAGE_META[pathname] ?? PAGE_META['/'];
  const onlineCount = AGENTS.filter((agent) => agent.status === 'online').length;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand__mark" aria-hidden="true">
            O
          </div>
          <div>
            <p className="brand__name">Oracle MAS</p>
            <p className="brand__sub">Agent Console</p>
          </div>
        </div>

        <nav className="nav" aria-label="Main navigation">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `nav__link${isActive ? ' nav__link--active' : ''}`}
            >
              <span className="nav__icon" aria-hidden="true">
                {item.icon}
              </span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar__footer">
          <div className="sidebar__status">
            <span className="badge__dot" aria-hidden="true" />
            {onlineCount}/{AGENTS.length} agents online
          </div>
          <p className="sidebar__mode">Demo mode · mocked API</p>
        </div>
      </aside>

      <div className="main-area">
        <header className="topbar">
          <div>
            <h1 className="topbar__title">{meta.title}</h1>
            <p className="topbar__subtitle">{meta.subtitle}</p>
          </div>
          <span className="topbar__pill">System operational</span>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
