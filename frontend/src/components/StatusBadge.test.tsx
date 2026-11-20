import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { StatusBadge } from './StatusBadge';

describe('StatusBadge', () => {
  it('renders the human-readable label and status style', () => {
    render(<StatusBadge status="completed" />);
    const badge = screen.getByText('Completed');
    expect(badge).toHaveClass('badge--completed');
  });

  it('supports agent statuses too', () => {
    render(<StatusBadge status="degraded" />);
    expect(screen.getByText('Degraded')).toHaveClass('badge--degraded');
  });
});
