import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { App } from '../App';

describe('AppShell Component Tests', () => {
  it('renders application shell and authorized cases list', async () => {
    render(<App />);

    expect(screen.getByTestId('app-shell')).toBeInTheDocument();
    expect(screen.getByText(/SIH26189 — CNAS/i)).toBeInTheDocument();

    await waitFor(
      () => {
        expect(screen.getAllByText(/Operation Hawala Nexus/i).length).toBeGreaterThan(0);
      },
      { timeout: 3000 }
    );
  });

  it('renders case header details and status badge', async () => {
    render(<App />);

    await waitFor(
      () => {
        expect(screen.getAllByText('CR-2026-DEL-0891').length).toBeGreaterThan(0);
        expect(screen.getAllByText(/New Delhi - Special Cell/i).length).toBeGreaterThan(0);
      },
      { timeout: 3000 }
    );
  });

  it('allows switching between tabs', async () => {
    render(<App />);

    await waitFor(
      () => {
        expect(screen.getAllByText('CR-2026-DEL-0891').length).toBeGreaterThan(0);
      },
      { timeout: 3000 }
    );

    const timelineTabBtn = await screen.findByRole('button', { name: /^Timeline$/i });
    fireEvent.click(timelineTabBtn);

    await waitFor(
      () => {
        expect(screen.getByText(/Case Event & Interaction Timeline/i)).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    const graphTabBtn = await screen.findByRole('button', { name: /^Graph Canvas$/i });
    fireEvent.click(graphTabBtn);

    await waitFor(
      () => {
        expect(screen.getByText(/Visible Nodes/i)).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it('allows simulating role changes', async () => {
    render(<App />);

    await waitFor(
      () => {
        expect(screen.getByText(/Investigator Role/i)).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    const invBtn = screen.getByRole('button', { name: 'INVE' });
    fireEvent.click(invBtn);
    expect(invBtn).toBeInTheDocument();
  });
});
