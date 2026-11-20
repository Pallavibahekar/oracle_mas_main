import { useState } from 'react';
import { RunResult } from '../components/RunResult';
import { StatusBadge } from '../components/StatusBadge';
import { AGENT_NAMES } from '../data/agents';
import { useRuns } from '../state/runs';
import type { RunStatus } from '../types';

type Filter = 'all' | RunStatus;

const FILTERS: Filter[] = ['all', 'completed', 'running', 'failed'];

export function RunsPage() {
  const { runs, clearHistory } = useRuns();
  const [filter, setFilter] = useState<Filter>('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const visibleRuns = filter === 'all' ? runs : runs.filter((run) => run.status === filter);

  return (
    <div className="page">
      <section className="section">
        <div className="section__header">
          <div className="filter-group" role="group" aria-label="Filter runs by status">
            {FILTERS.map((item) => (
              <button
                className={`filter-button${filter === item ? ' filter-button--active' : ''}`}
                key={item}
                type="button"
                onClick={() => setFilter(item)}
              >
                {item.charAt(0).toUpperCase() + item.slice(1)}
                <span className="filter-button__count">
                  {item === 'all' ? runs.length : runs.filter((run) => run.status === item).length}
                </span>
              </button>
            ))}
          </div>
          {runs.length > 0 && (
            <button className="button button--ghost" type="button" onClick={clearHistory}>
              Clear history
            </button>
          )}
        </div>

        {visibleRuns.length === 0 ? (
          <div className="empty-state">
            <p>No runs match this filter.</p>
          </div>
        ) : (
          <div className="runs-list">
            {visibleRuns.map((run) => {
              const isExpanded = expandedId === run.id;
              return (
                <article className="run-row" key={run.id}>
                  <button
                    className="run-row__summary"
                    type="button"
                    aria-expanded={isExpanded}
                    onClick={() => setExpandedId(isExpanded ? null : run.id)}
                  >
                    <span className="run-row__chevron" aria-hidden="true">
                      {isExpanded ? '▾' : '▸'}
                    </span>
                    <span className="run-row__query">{run.query}</span>
                    <span className="run-row__route">
                      {run.route.map((id) => AGENT_NAMES[id]).join(' → ')}
                    </span>
                    <span className="run-row__date">
                      {new Date(run.createdAt).toLocaleString([], {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                    <StatusBadge status={run.status} />
                  </button>
                  {isExpanded && (
                    <div className="run-row__detail">
                      <RunResult run={run} />
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
