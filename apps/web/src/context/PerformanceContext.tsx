import React, { createContext, useContext, useState, useEffect } from 'react';
import { PerformanceMode } from '../types';

interface PerformanceContextType {
  mode: PerformanceMode;
  setMode: (mode: PerformanceMode) => void;
  is3dEnabled: boolean;
  isSmoothScrollEnabled: boolean;
  isHighParticleDensity: boolean;
}

const PerformanceContext = createContext<PerformanceContextType | undefined>(undefined);

export const PerformanceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Check prefers-reduced-motion
  const [mode, setMode] = useState<PerformanceMode>(() => {
    if (typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return 'reduced';
    }
    return 'full';
  });

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handleChange = (e: MediaQueryListEvent) => {
      if (e.matches) {
        setMode('reduced');
      }
    };
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  const is3dEnabled = mode !== 'reduced';
  const isSmoothScrollEnabled = mode === 'full';
  const isHighParticleDensity = mode === 'full';

  return (
    <PerformanceContext.Provider
      value={{
        mode,
        setMode,
        is3dEnabled,
        isSmoothScrollEnabled,
        isHighParticleDensity,
      }}
    >
      {children}
    </PerformanceContext.Provider>
  );
};

export const usePerformance = () => {
  const context = useContext(PerformanceContext);
  if (!context) {
    throw new Error('usePerformance must be used within a PerformanceProvider');
  }
  return context;
};
