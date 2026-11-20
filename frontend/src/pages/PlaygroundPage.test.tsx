import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { RunsProvider } from '../state/runs';
import { PlaygroundPage } from './PlaygroundPage';

function renderPlayground() {
  return render(
    <RunsProvider streamDelayMs={0}>
      <PlaygroundPage />
    </RunsProvider>,
  );
}

describe('PlaygroundPage', () => {
  it('streams agent activity and renders a synthesized answer', async () => {
    const user = userEvent.setup();
    renderPlayground();

    await user.type(
      screen.getByLabelText('Ask the agent swarm'),
      'Summarize the policy document{Enter}',
    );

    expect(await screen.findByText('Classifying intent')).toBeInTheDocument();
    expect(await screen.findByText(/I routed/)).toBeInTheDocument();
    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.getAllByText(/Vector DB/).length).toBeGreaterThan(0);
  });

  it('does not start a run with an empty query', async () => {
    const user = userEvent.setup();
    renderPlayground();

    const button = screen.getByRole('button', { name: /run agents/i });
    expect(button).toBeDisabled();

    await user.click(screen.getByRole('button', { name: /summarize our remote work policy/i }));
    expect(screen.getByLabelText('Ask the agent swarm')).toHaveValue(
      'Summarize our remote work policy from the handbook',
    );
    expect(button).toBeEnabled();
  });
});
