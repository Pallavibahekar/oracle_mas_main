import { describe, expect, it } from 'vitest';
import { chooseRoute, streamRun, type RunEvent } from './mockApi';

async function collect(query: string, signal?: AbortSignal): Promise<RunEvent[]> {
  const events: RunEvent[] = [];
  for await (const event of streamRun(query, { delayMs: 0, signal })) {
    events.push(event);
  }
  return events;
}

describe('chooseRoute', () => {
  it('sends internal knowledge requests to the data sources agent', () => {
    expect(chooseRoute('Summarize the remote work policy document')).toEqual([
      'router',
      'data-sources',
    ]);
  });

  it('sends freshness requests to the internet search agent', () => {
    expect(chooseRoute('What are the latest updates?')).toEqual([
      'router',
      'internet-search',
    ]);
  });

  it('fans out when both internal and web context are needed', () => {
    expect(chooseRoute('Compare our contract with market benchmarks')).toEqual([
      'router',
      'data-sources',
      'internet-search',
    ]);
  });

  it('fans out on ambiguous requests', () => {
    expect(chooseRoute('Help me decide')).toHaveLength(3);
  });
});

describe('streamRun', () => {
  it('emits start, one event per step, then complete', async () => {
    const events = await collect('Summarize the policy document');
    expect(events.map((event) => event.type)).toEqual([
      'start',
      'step',
      'step',
      'complete',
    ]);

    if (events[0].type !== 'start' || events[3].type !== 'complete') {
      throw new Error('Unexpected event shape');
    }
    expect(events[0].run.status).toBe('running');
    expect(events[0].run.route).toEqual(['router', 'data-sources']);
    expect(events[3].sources.length).toBeGreaterThan(0);
    expect(events[3].answer).toContain('Router Agent');
  });

  it('reports an empty query as an error instead of starting a run', async () => {
    const events = await collect('   ');
    expect(events).toHaveLength(1);
    expect(events[0].type).toBe('error');
  });
});
