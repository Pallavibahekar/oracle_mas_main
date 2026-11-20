import type { Agent, AgentId } from '../types';

export const AGENTS: Agent[] = [
  {
    id: 'router',
    name: 'Router Agent',
    role: 'Orchestrator',
    description:
      'Classifies each incoming request and delegates it to the right specialist. Owns the final synthesis step.',
    capabilities: ['Intent classification', 'Task delegation', 'Response synthesis'],
    status: 'online',
    model: 'Llama 4 Scout · Bedrock',
    avgLatencyMs: 210,
  },
  {
    id: 'data-sources',
    name: 'Data Sources Agent',
    role: 'Retrieval specialist',
    description:
      'Queries the internal knowledge base through an MCP RAG tool backed by Qdrant vector search.',
    capabilities: ['Vector search', 'RAG grounding', 'Document citations'],
    status: 'online',
    model: 'Llama 4 Scout · Bedrock',
    avgLatencyMs: 480,
  },
  {
    id: 'internet-search',
    name: 'Internet Search Agent',
    role: 'Web researcher',
    description:
      'Searches the public web for fresh context, then summarizes findings with source links.',
    capabilities: ['Web search', 'Freshness checks', 'Source linking'],
    status: 'online',
    model: 'Llama 4 Scout · Bedrock',
    avgLatencyMs: 640,
  },
];

export const AGENT_BY_ID: Record<AgentId, Agent> = AGENTS.reduce(
  (acc, agent) => ({ ...acc, [agent.id]: agent }),
  {} as Record<AgentId, Agent>,
);

export const AGENT_NAMES: Record<AgentId, string> = {
  router: 'Router',
  'data-sources': 'Data Sources',
  'internet-search': 'Internet Search',
};
