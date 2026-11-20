import type { Agent } from '../types';
import { StatusBadge } from './StatusBadge';

interface AgentCardProps {
  agent: Agent;
  compact?: boolean;
}

export function AgentCard({ agent, compact = false }: AgentCardProps) {
  return (
    <article className={`agent-card${compact ? ' agent-card--compact' : ''}`}>
      <header className="agent-card__header">
        <div className="agent-card__avatar" aria-hidden="true">
          {agent.name.charAt(0)}
        </div>
        <div>
          <h3 className="agent-card__name">{agent.name}</h3>
          <p className="agent-card__role">{agent.role}</p>
        </div>
        <StatusBadge status={agent.status} />
      </header>

      {!compact && <p className="agent-card__description">{agent.description}</p>}

      <ul className="chips" aria-label={`${agent.name} capabilities`}>
        {agent.capabilities.map((capability) => (
          <li className="chip" key={capability}>
            {capability}
          </li>
        ))}
      </ul>

      <footer className="agent-card__footer">
        <span className="agent-card__meta">{agent.model}</span>
        <span className="agent-card__meta">~{agent.avgLatencyMs} ms</span>
      </footer>
    </article>
  );
}
