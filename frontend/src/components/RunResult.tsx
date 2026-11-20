import type { AgentRun } from '../types';
import { StepTimeline } from './StepTimeline';

interface RunResultProps {
  run: AgentRun;
  showQuery?: boolean;
}

export function RunResult({ run, showQuery = false }: RunResultProps) {
  return (
    <div className="run-result">
      {showQuery && (
        <div className="run-result__query">
          <span className="eyebrow">Your request</span>
          <p>{run.query}</p>
        </div>
      )}

      <div className="run-result__grid">
        <section className="panel">
          <h3 className="panel__title">Agent activity</h3>
          <StepTimeline steps={run.steps} isRunning={run.status === 'running'} />
        </section>

        <section className="panel">
          <h3 className="panel__title">Response</h3>
          {run.answer ? (
            <p className="run-result__answer">{run.answer}</p>
          ) : run.status === 'failed' ? (
            <p className="run-result__answer run-result__answer--error">
              This run failed before the router could synthesize a response.
            </p>
          ) : (
            <p className="muted">Waiting for the swarm to finish…</p>
          )}

          {run.sources.length > 0 && (
            <>
              <h4 className="panel__subtitle">Sources</h4>
              <ul className="source-list">
                {run.sources.map((source) => (
                  <li key={source.url}>
                    <span className={`source-list__tag source-list__tag--${source.kind}`}>
                      {source.kind === 'web' ? 'Web' : 'Vector DB'}
                    </span>
                    <a href={source.url} target="_blank" rel="noreferrer">
                      {source.title}
                    </a>
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
