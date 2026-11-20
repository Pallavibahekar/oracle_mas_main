import { AgentCard } from '../components/AgentCard';
import { AGENTS } from '../data/agents';

const ROUTING_RULES = [
  {
    condition: 'Internal / document keywords',
    route: 'Router → Data Sources',
    example: '“Summarize the remote work policy”',
  },
  {
    condition: 'Freshness / web keywords',
    route: 'Router → Internet Search',
    example: '“Latest MCP updates”',
  },
  {
    condition: 'Mixed or ambiguous request',
    route: 'Router → both specialists',
    example: '“Compare our contracts with the market”',
  },
];

export function AgentsPage() {
  return (
    <div className="page">
      <section className="section">
        <div className="agent-grid agent-grid--wide">
          {AGENTS.map((agent) => (
            <AgentCard agent={agent} key={agent.id} />
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section__header">
          <div>
            <h2 className="section__title">How routing works</h2>
            <p className="section__subtitle">
              The router classifies intent before delegating. The demo uses a deterministic
              keyword rule; production uses the LangGraph router agent.
            </p>
          </div>
        </div>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col">Condition</th>
                <th scope="col">Selected route</th>
                <th scope="col">Example</th>
              </tr>
            </thead>
            <tbody>
              {ROUTING_RULES.map((rule) => (
                <tr key={rule.condition}>
                  <td>{rule.condition}</td>
                  <td>
                    <code>{rule.route}</code>
                  </td>
                  <td className="muted">{rule.example}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
