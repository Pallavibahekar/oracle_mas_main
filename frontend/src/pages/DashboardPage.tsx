import { Link } from 'react-router-dom';
import { AgentCard } from '../components/AgentCard';
import { StatusBadge } from '../components/StatusBadge';
import { AGENTS, AGENT_NAMES } from '../data/agents';
import { useRuns } from '../state/runs';

export function DashboardPage() {
  const { runs } = useRuns();
  const completed = runs.filter((run) => run.status === 'completed');
  const successRate = runs.length
    ? Math.round((completed.length / runs.length) * 100)
    : 0;
  const durations = completed.flatMap((run) =>
    run.steps.map((step) => step.durationMs),
  );
  const avgLatency = durations.length
    ? Math.round(durations.reduce((sum, value) => sum + value, 0) / durations.length)
    : 0;

  const stats = [
    { label: 'Total runs', value: String(runs.length), hint: 'This session' },
    { label: 'Success rate', value: `${successRate}%`, hint: 'Completed / total' },
    { label: 'Avg step latency', value: `${avgLatency} ms`, hint: 'Across all agents' },
    { label: 'Active agents', value: String(AGENTS.length), hint: 'Router + 2 specialists' },
  ];

  return (
    <div className="page">
      <section className="stats-grid" aria-label="Key metrics">
        {stats.map((stat) => (
          <article className="stat-card" key={stat.label}>
            <p className="stat-card__label">{stat.label}</p>
            <p className="stat-card__value">{stat.value}</p>
            <p className="stat-card__hint">{stat.hint}</p>
          </article>
        ))}
      </section>

      <section className="section">
        <div className="section__header">
          <div>
            <h2 className="section__title">Agent fleet</h2>
            <p className="section__subtitle">Three cooperating agents, one entry point.</p>
          </div>
          <Link className="button button--ghost" to="/agents">
            View agents →
          </Link>
        </div>
        <div className="agent-grid">
          {AGENTS.slice(0, 2).map((agent) => (
            <AgentCard agent={agent} key={agent.id} compact />
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section__header">
          <div>
            <h2 className="section__title">Recent runs</h2>
            <p className="section__subtitle">Latest orchestrations across the swarm.</p>
          </div>
          <Link className="button button--ghost" to="/runs">
            Full history →
          </Link>
        </div>

        {runs.length === 0 ? (
          <div className="empty-state">
            <p>No runs yet. Start one from the playground.</p>
            <Link className="button button--primary" to="/playground">
              Open playground
            </Link>
          </div>
        ) : (
          <div className="recent-list">
            {runs.slice(0, 4).map((run) => (
              <article className="recent-item" key={run.id}>
                <div className="recent-item__main">
                  <p className="recent-item__query">{run.query}</p>
                  <p className="recent-item__meta">
                    {run.route.map((id) => AGENT_NAMES[id]).join(' → ')} ·{' '}
                    {new Date(run.createdAt).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
                <StatusBadge status={run.status} />
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
