import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { createSeedRuns, streamRun } from '../services/mockApi';
import type { AgentRun } from '../types';

interface RunsContextValue {
  runs: AgentRun[];
  activeRun: AgentRun | null;
  error: string | null;
  isRunning: boolean;
  startRun: (query: string) => Promise<AgentRun | null>;
  clearHistory: () => void;
  streamDelayMs: number;
}

const RunsContext = createContext<RunsContextValue | null>(null);

interface RunsProviderProps {
  children: ReactNode;
  /** Kept configurable so tests can run the stream without real delays. */
  streamDelayMs?: number;
}

export function RunsProvider({ children, streamDelayMs = 320 }: RunsProviderProps) {
  const [runs, setRuns] = useState<AgentRun[]>(() => createSeedRuns());
  const [activeRun, setActiveRun] = useState<AgentRun | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const startRun = useCallback(
    async (query: string): Promise<AgentRun | null> => {
      if (!query.trim() || isRunning) {
        return null;
      }

      setIsRunning(true);
      setError(null);
      setActiveRun(null);

      // A local accumulator keeps the stream reducer pure: no nested setState
      // side effects. A holder object avoids self-referential TS narrowing.
      const accumulator: { run: AgentRun | null } = { run: null };

      for await (const event of streamRun(query, { delayMs: streamDelayMs })) {
        switch (event.type) {
          case 'start': {
            accumulator.run = { ...event.run };
            setActiveRun(accumulator.run);
            break;
          }
          case 'step': {
            const current = accumulator.run;
            if (current) {
              const next: AgentRun = {
                ...current,
                steps: [...current.steps, event.step],
              };
              accumulator.run = next;
              setActiveRun(next);
            }
            break;
          }
          case 'complete': {
            const current = accumulator.run;
            if (current) {
              const completed: AgentRun = {
                ...current,
                status: 'completed',
                answer: event.answer,
                sources: event.sources,
              };
              accumulator.run = completed;
              setActiveRun(completed);
              setRuns((existing) => [completed, ...existing]);
            }
            break;
          }
          case 'error': {
            setError(event.message);
            const current = accumulator.run;
            if (current) {
              const failed: AgentRun = { ...current, status: 'failed' };
              accumulator.run = failed;
              setActiveRun(failed);
            }
            break;
          }
        }
      }

      setIsRunning(false);
      return accumulator.run;
    },
    [isRunning, streamDelayMs],
  );

  const clearHistory = useCallback(() => {
    setRuns([]);
    setActiveRun(null);
    setError(null);
  }, []);

  const value = useMemo<RunsContextValue>(
    () => ({ runs, activeRun, error, isRunning, startRun, clearHistory, streamDelayMs }),
    [runs, activeRun, error, isRunning, startRun, clearHistory, streamDelayMs],
  );

  return <RunsContext.Provider value={value}>{children}</RunsContext.Provider>;
}

export function useRuns(): RunsContextValue {
  const context = useContext(RunsContext);
  if (!context) {
    throw new Error('useRuns must be used inside a RunsProvider');
  }
  return context;
}
