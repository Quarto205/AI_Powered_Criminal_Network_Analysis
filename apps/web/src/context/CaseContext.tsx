/**
 * Case & Authorization Context
 * Manages active case, case switching, and role-based permissions.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { CaseListItem, CaseDetailResponse } from '../contracts/cases';
import { UserRole } from '../contracts/common';
import { apiClient } from '../api';
import { DEMO_CASE_ID } from '../fixtures';

interface CaseContextType {
  cases: CaseListItem[];
  activeCaseId: string | null;
  activeCase: CaseDetailResponse | null;
  currentRole: UserRole;
  setCurrentRole: (role: UserRole) => void;
  selectCase: (caseId: string) => void;
  loading: boolean;
  error: string | null;
  refreshCase: () => Promise<void>;
}

export const CaseContext = createContext<CaseContextType | undefined>(undefined);

export const CaseProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [activeCaseId, setActiveCaseId] = useState<string | null>(DEMO_CASE_ID);
  const [activeCase, setActiveCase] = useState<CaseDetailResponse | null>(null);
  const [currentRole, setCurrentRole] = useState<UserRole>('SUPERVISOR');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCases = useCallback(async () => {
    try {
      const resp = await apiClient.listCases();
      setCases(resp.data.cases);
      if (!activeCaseId && resp.data.cases.length > 0) {
        setActiveCaseId(resp.data.cases[0].case_id);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load cases');
    }
  }, [activeCaseId]);

  const fetchActiveCase = useCallback(async (caseId: string) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await apiClient.getCase(caseId);
      setActiveCase(resp.data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : `Failed to load case ${caseId}`);
      setActiveCase(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCases();
  }, [fetchCases]);

  useEffect(() => {
    if (activeCaseId) {
      fetchActiveCase(activeCaseId);
    }
  }, [activeCaseId, fetchActiveCase]);

  const selectCase = (caseId: string) => {
    setActiveCaseId(caseId);
  };

  const refreshCase = async () => {
    if (activeCaseId) {
      await fetchActiveCase(activeCaseId);
    }
  };

  return (
    <CaseContext.Provider
      value={{
        cases,
        activeCaseId,
        activeCase,
        currentRole,
        setCurrentRole,
        selectCase,
        loading,
        error,
        refreshCase,
      }}
    >
      {children}
    </CaseContext.Provider>
  );
};

export const useCase = (): CaseContextType => {
  const context = useContext(CaseContext);
  if (!context) {
    throw new Error('useCase must be used within a CaseProvider');
  }
  return context;
};
