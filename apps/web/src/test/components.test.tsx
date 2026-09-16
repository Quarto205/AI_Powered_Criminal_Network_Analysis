import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { Badge } from '../components/ui/Badge';
import { AnimatedCounter } from '../components/ui/AnimatedCounter';
import { PerformanceProvider } from '../context/PerformanceContext';
import { CaseProvider, useCase } from '../context/CaseContext';
import { AuthProvider } from '../context/AuthContext';

describe('CNAS UI Components & Contexts', () => {
  it('renders Badge with verified variant', () => {
    render(<Badge variant="verified">Source Verified</Badge>);
    expect(screen.getByText('Source Verified')).toBeInTheDocument();
  });

  it('renders Badge with AI inferred dashed variant', () => {
    render(<Badge variant="ai-inferred">AI Predicted (94%)</Badge>);
    expect(screen.getByText('AI Predicted (94%)')).toBeInTheDocument();
  });

  it('renders AnimatedCounter with formatted values', () => {
    render(
      <PerformanceProvider>
        <AnimatedCounter value={14} />
      </PerformanceProvider>
    );
    expect(screen.getByText(/14|00/)).toBeInTheDocument();
  });

  it('verifies CaseContext cross-workspace Inspect in Graph pivot', async () => {
    const TestComponent = () => {
      const { activeTab, selectedEntity, isDrawerOpen, inspectInGraph } = useCase();
      return (
        <div>
          <span data-testid="tab">{activeTab}</span>
          <span data-testid="drawer">{isDrawerOpen ? 'open' : 'closed'}</span>
          <span data-testid="entity">{selectedEntity?.name}</span>
          <button onClick={() => inspectInGraph('ent-tariq')}>Inspect Tariq</button>
        </div>
      );
    };

    render(
      <AuthProvider>
        <CaseProvider>
          <TestComponent />
        </CaseProvider>
      </AuthProvider>
    );

    expect(screen.getByTestId('tab').textContent).toBe('copilot');
    
    // Trigger inspect in graph wrapped in act
    await act(async () => {
      fireEvent.click(screen.getByText('Inspect Tariq'));
    });

    expect(screen.getByTestId('tab').textContent).toBe('network');
    expect(screen.getByTestId('drawer').textContent).toBe('open');
    expect(screen.getByTestId('entity').textContent).toBe('Tariq M.');
  });
});
