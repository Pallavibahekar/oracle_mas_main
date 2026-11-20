import { useState, type FormEvent, type KeyboardEvent } from 'react';

const EXAMPLES = [
  'Summarize our remote work policy from the handbook',
  'What are the latest updates to MCP?',
  'Compare our contract terms with market benchmarks',
];

interface QueryComposerProps {
  onSubmit: (query: string) => void;
  isRunning: boolean;
}

export function QueryComposer({ onSubmit, isRunning }: QueryComposerProps) {
  const [query, setQuery] = useState('');

  const submit = () => {
    if (!query.trim() || isRunning) {
      return;
    }
    onSubmit(query.trim());
    setQuery('');
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    submit();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  };

  return (
    <section className="composer" aria-label="Agent playground">
      <form onSubmit={handleSubmit}>
        <label className="composer__label" htmlFor="agent-query">
          Ask the agent swarm
        </label>
        <div className="composer__box">
          <textarea
            id="agent-query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about internal documents, live web research, or both…"
            rows={3}
            disabled={isRunning}
          />
          <button className="button button--primary" type="submit" disabled={isRunning || !query.trim()}>
            {isRunning ? 'Running…' : 'Run agents'}
          </button>
        </div>
      </form>

      <div className="composer__examples">
        <span>Try:</span>
        {EXAMPLES.map((example) => (
          <button
            className="example-chip"
            key={example}
            type="button"
            disabled={isRunning}
            onClick={() => setQuery(example)}
          >
            {example}
          </button>
        ))}
      </div>
    </section>
  );
}
