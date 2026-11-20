import { AGENT_NAMES } from '../data/agents';
import type { RunStep } from '../types';

interface StepTimelineProps {
  steps: RunStep[];
  isRunning?: boolean;
}

export function StepTimeline({ steps, isRunning = false }: StepTimelineProps) {
  if (steps.length === 0) {
    return (
      <div className="empty-state empty-state--inline">
        <p>{isRunning ? 'Waiting for the router…' : 'No agent activity yet.'}</p>
      </div>
    );
  }

  return (
    <ol className="timeline" aria-label="Agent activity">
      {steps.map((step, index) => (
        <li className="timeline__item" key={step.id}>
          <div
            className={`timeline__marker${step.status === 'error' ? ' timeline__marker--error' : ''}`}
            aria-hidden="true"
          >
            {step.status === 'error' ? '!' : index + 1}
          </div>
          <div className="timeline__body">
            <div className="timeline__heading">
              <strong>{AGENT_NAMES[step.agent]}</strong>
              <span className="timeline__action">{step.action}</span>
              <span className="timeline__duration">{step.durationMs} ms</span>
            </div>
            <p className="timeline__detail">{step.detail}</p>
          </div>
        </li>
      ))}
      {isRunning && (
        <li className="timeline__item timeline__item--pending">
          <div className="timeline__marker timeline__marker--pulse" aria-hidden="true" />
          <div className="timeline__body">
            <div className="timeline__heading">
              <strong>Agent swarm</strong>
              <span className="timeline__action">Working…</span>
            </div>
          </div>
        </li>
      )}
    </ol>
  );
}
