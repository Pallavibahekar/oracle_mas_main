import type { AgentStatus, RunStatus } from '../types';

type BadgeStatus = AgentStatus | RunStatus;

const LABELS: Record<BadgeStatus, string> = {
  online: 'Online',
  busy: 'Busy',
  degraded: 'Degraded',
  offline: 'Offline',
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
};

export function StatusBadge({ status }: { status: BadgeStatus }) {
  return (
    <span className={`badge badge--${status}`}>
      <span className="badge__dot" aria-hidden="true" />
      {LABELS[status]}
    </span>
  );
}
