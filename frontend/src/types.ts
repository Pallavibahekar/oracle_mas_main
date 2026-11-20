export type AgentId = 'router' | 'data-sources' | 'internet-search';

export type AgentStatus = 'online' | 'busy' | 'degraded' | 'offline';

export interface Agent {
  id: AgentId;
  name: string;
  role: string;
  description: string;
  capabilities: string[];
  status: AgentStatus;
  model: string;
  avgLatencyMs: number;
}

export type RunStatus = 'running' | 'completed' | 'failed';

export type StepStatus = 'ok' | 'active' | 'queued' | 'error';

export interface RunStep {
  id: string;
  agent: AgentId;
  action: string;
  detail: string;
  durationMs: number;
  status: StepStatus;
}

export interface Source {
  title: string;
  url: string;
  kind: 'vector-db' | 'web';
}

export interface AgentRun {
  id: string;
  query: string;
  route: AgentId[];
  status: RunStatus;
  createdAt: string;
  steps: RunStep[];
  answer: string;
  sources: Source[];
}
