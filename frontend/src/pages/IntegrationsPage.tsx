const INTEGRATIONS = [
  {
    name: 'AWS Bedrock',
    kind: 'LLM provider',
    detail: 'Llama 4 Scout via ChatBedrockConverse powers each agent’s reasoning loop.',
    state: 'Requires credentials',
  },
  {
    name: 'Qdrant',
    kind: 'Vector database',
    detail: 'Stores policy and contract embeddings for the MCP RAG retrieval tool.',
    state: 'Requires local service',
  },
  {
    name: 'Neo4j',
    kind: 'Graph database',
    detail: 'Available through docker-compose for relationship-aware data sources.',
    state: 'Requires local service',
  },
  {
    name: 'MCP tools',
    kind: 'Tool layer',
    detail: 'LangChain MCP adapters expose RAG and search tools to the agent graph.',
    state: 'Configured in backend',
  },
  {
    name: 'A2A protocol',
    kind: 'Agent communication',
    detail: 'Agent cards and task streams let agents delegate work to each other.',
    state: 'Implemented in backend',
  },
];

export function IntegrationsPage() {
  return (
    <div className="page">
      <div className="notice">
        <strong>Demo mode is intentional.</strong> This console ships with a typed mock event
        stream so it runs without AWS keys or local databases. The integration list below mirrors
        the real Python services; replacing <code>mockApi.streamRun</code> with an SSE client is the
        only change needed to go live.
      </div>

      <section className="section">
        <div className="integration-grid">
          {INTEGRATIONS.map((item) => (
            <article className="integration-card" key={item.name}>
              <p className="eyebrow">{item.kind}</p>
              <h3>{item.name}</h3>
              <p className="muted">{item.detail}</p>
              <p className="integration-card__state">{item.state}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
