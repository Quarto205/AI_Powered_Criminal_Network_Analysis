import React, { useState, useEffect } from 'react';
import Lenis from 'lenis';
import { useAuth } from './context/AuthContext';
import { useCase } from './context/CaseContext';
import { usePerformance } from './context/PerformanceContext';
import { AppHeader } from './components/shell/AppHeader';
import { AppSidebar } from './components/shell/AppSidebar';
import { CommandPalette } from './components/shell/CommandPalette';
import { JobsDrawer } from './components/shell/JobsDrawer';

// Views
import { LoginView } from './views/LoginView';
import { CasesView } from './views/CasesView';
import { OverviewView } from './views/OverviewView';
import { GraphView } from './views/GraphView';
import { TimelineView } from './views/TimelineView';
import { EvidenceView } from './views/EvidenceView';
import { AnalysisView } from './views/AnalysisView';
import { CopilotView } from './views/CopilotView';
import { AuditView } from './views/AuditView';

export const App: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const { activeTab } = useCase();
  const { isSmoothScrollEnabled } = usePerformance();
  const [isJobsOpen, setIsJobsOpen] = useState<boolean>(false);

  // Lenis Smooth Scroll lifecycle
  useEffect(() => {
    if (!isSmoothScrollEnabled || !isAuthenticated || activeTab === 'network') {
      return;
    }

    const lenis = new Lenis({
      duration: 1.1,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: 'vertical',
      gestureOrientation: 'vertical',
      smoothWheel: true,
      wheelMultiplier: 0.9,
    });

    let rafId: number;
    const raf = (time: number) => {
      lenis.raf(time);
      rafId = requestAnimationFrame(raf);
    };
    rafId = requestAnimationFrame(raf);

    return () => {
      cancelAnimationFrame(rafId);
      lenis.destroy();
    };
  }, [isSmoothScrollEnabled, isAuthenticated, activeTab]);

  if (!isAuthenticated) {
    return <LoginView />;
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: 'var(--cnas-bg)' }}>
      {/* Top Fixed Header */}
      <AppHeader onOpenJobsDrawer={() => setIsJobsOpen(true)} />

      {/* Left Fixed Navigation Rail */}
      <AppSidebar />

      {/* Main Investigative Working Canvas */}
      <main
        style={{
          marginLeft: '240px',
          marginTop: '64px',
          flex: 1,
          padding: '1.5rem 2rem',
          minWidth: 0,
          minHeight: 'calc(100vh - 64px)',
          backgroundColor: 'var(--cnas-bg)',
        }}
      >
        {activeTab === 'cases' && <CasesView />}
        {activeTab === 'overview' && <OverviewView />}
        {activeTab === 'network' && <GraphView />}
        {activeTab === 'timeline' && <TimelineView />}
        {activeTab === 'evidence' && <EvidenceView />}
        {activeTab === 'analysis' && <AnalysisView />}
        {activeTab === 'copilot' && <CopilotView />}
        {activeTab === 'audit' && <AuditView />}
      </main>

      {/* Global Command Palette (⌘K) */}
      <CommandPalette />

      {/* Real-time Ingestion & Extraction Jobs Drawer */}
      <JobsDrawer isOpen={isJobsOpen} onClose={() => setIsJobsOpen(false)} />
    </div>
  );
};
