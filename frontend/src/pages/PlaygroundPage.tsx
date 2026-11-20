import { QueryComposer } from '../components/QueryComposer';
import { RunResult } from '../components/RunResult';
import { StatusBadge } from '../components/StatusBadge';
import { useRuns } from '../state/runs';

export function PlaygroundPage() {
  const { activeRun, error, isRunning, startRun } = useRuns();

  return (
    <div className="page">
      <QueryComposer onSubmit={startRun} isRunning={isRunning} />

      {error && (
        <div className="alert alert--error" role="alert">
          {error}
        </div>
      )}

      {activeRun ? (
        <section className="section" aria-live="polite">
          <div className="section__header">
            <div>
              <h2 className="section__title">Current run</h2>
              <p className="section__subtitle">
                {activeRun.route.length} agent{activeRun.route.length === 1 ? '' : 's'} selected
              </p>
            </div>
            <StatusBadge status={activeRun.status} />
          </div>
          <RunResult run={activeRun} showQuery />
        </section>
      ) : (
        <div className="empty-state">
          <p className="empty-state__icon" aria-hidden="true">
            ⌘
          </p>
          <p>Ask a question to see the router pick agents and stream their results here.</p>
        </div>
      )}
    </div>
  );
}
