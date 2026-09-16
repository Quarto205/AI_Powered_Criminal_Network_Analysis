import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../services/apiClient';
import {
  CaseFile,
  EntityDossier,
  EvidenceDocument,
  TimelineEvent,
  PriorityLead
} from '../types';
import {
  INITIAL_CASES,
  MOCK_ENTITIES,
  MOCK_EVIDENCE_DOCS,
  MOCK_TIMELINE_EVENTS,
  MOCK_PRIORITY_LEADS,
  CURRENT_INVESTIGATOR
} from '../mocks/data';

export type WorkspaceTab =
  | 'overview'
  | 'network'
  | 'timeline'
  | 'evidence'
  | 'analysis'
  | 'copilot'
  | 'audit'
  | 'cases';

interface CaseContextType {
  cases: CaseFile[];
  activeCase: CaseFile;
  setActiveCase: (c: CaseFile) => void;
  activeTab: WorkspaceTab;
  setActiveTab: (tab: WorkspaceTab) => void;
  entities: EntityDossier[];
  selectedEntity: EntityDossier | null;
  setSelectedEntity: (entity: EntityDossier | null) => void;
  isDrawerOpen: boolean;
  setIsDrawerOpen: (open: boolean) => void;
  evidenceDocs: EvidenceDocument[];
  selectedDoc: EvidenceDocument | null;
  setSelectedDoc: (doc: EvidenceDocument | null) => void;
  timelineEvents: TimelineEvent[];
  priorityLeads: PriorityLead[];
  inspectInGraph: (entityId: string) => void;
  viewDocumentDossier: (docId: string) => void;
  addEvidenceDocument: (doc: EvidenceDocument) => void;
}

const CaseContext = createContext<CaseContextType | undefined>(undefined);

export const CaseProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [cases, setCases] = useState<CaseFile[]>(INITIAL_CASES);
  const [activeCase, setActiveCase] = useState<CaseFile>(INITIAL_CASES[0]);
  const [activeTab, setActiveTab] = useState<WorkspaceTab>('copilot');
  const [entities] = useState<EntityDossier[]>(MOCK_ENTITIES);
  const [selectedEntity, setSelectedEntity] = useState<EntityDossier | null>(MOCK_ENTITIES[0]);
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);
  const [evidenceDocs, setEvidenceDocs] = useState<EvidenceDocument[]>(MOCK_EVIDENCE_DOCS);
  const [selectedDoc, setSelectedDoc] = useState<EvidenceDocument | null>(null);
  const [timelineEvents] = useState<TimelineEvent[]>(MOCK_TIMELINE_EVENTS);
  const [priorityLeads] = useState<PriorityLead[]>(MOCK_PRIORITY_LEADS);

  useEffect(() => {
    const fetchCases = async () => {
      try {
        const res = await apiClient.get<any>('/api/v1/cases');
        if (res.success && res.data && res.data.cases) {
          const mappedCases: CaseFile[] = res.data.cases.map((c: any) => ({
            id: c.case_id || c.id,
            caseNumber: c.case_code || 'N/A',
            title: c.title,
            jurisdiction: c.jurisdiction || 'Federal',
            unit: 'Special Cell', // Fallback
            status: c.status as any || 'ACTIVE',
            stage: 'Investigation',
            leadInvestigator: CURRENT_INVESTIGATOR, // Fallback
            entityCount: c.entity_count || 0,
            evidenceCount: c.evidence_count || 0,
            criticalLeadsCount: 0,
            description: c.description || 'No description provided.',
            createdAt: c.created_at,
            updatedAt: c.updated_at || c.created_at,
          }));
          
          if (mappedCases.length > 0) {
            setCases(mappedCases);
            setActiveCase(mappedCases[0]);
          }
        }
      } catch (e) {
        console.error("Failed to fetch cases from backend:", e);
      }
    };

    // We can only fetch if token is present, but apiClient handles adding the token.
    if (apiClient.getToken()) {
      fetchCases();
    }
  }, []);

  useEffect(() => {
    const fetchDocuments = async () => {
      if (!activeCase?.id) return;
      try {
        const res = await apiClient.get<any>(`/api/v1/cases/${activeCase.id}/documents`);
        if (res.success && res.data && res.data.documents) {
          const mappedDocs: EvidenceDocument[] = res.data.documents.map((d: any) => ({
            id: d.document_id,
            caseId: d.case_id,
            title: d.filename || 'Unknown Document',
            filename: d.filename || 'unknown.pdf',
            category: 'BANKING', // Mocked category mapping
            sha256: d.file_hash || 'unknown',
            fileSize: 'Unknown Size',
            timestamp: d.uploaded_at || new Date().toISOString(),
            verifiedChainOfCustody: true,
            section65BCertified: true,
            linkedEntityIds: [],
            excerpt: 'No excerpt available.',
            metadata: {},
          }));
          setEvidenceDocs(mappedDocs);
        }
      } catch (e) {
        console.error("Failed to fetch documents from backend:", e);
      }
    };
    
    if (apiClient.getToken()) {
      fetchDocuments();
    }
  }, [activeCase?.id]);

  // Cross-workspace navigation: Inspect in Graph
  const inspectInGraph = (entityId: string) => {
    const ent = entities.find((e) => e.id === entityId) || entities[0];
    setSelectedEntity(ent);
    setIsDrawerOpen(true);
    setActiveTab('network');
  };

  // Cross-workspace navigation: View Document Dossier
  const viewDocumentDossier = (docId: string) => {
    const doc = evidenceDocs.find((d) => d.id === docId) || evidenceDocs[0];
    setSelectedDoc(doc);
    setActiveTab('evidence');
  };

  const addEvidenceDocument = (newDoc: EvidenceDocument) => {
    setEvidenceDocs((prev) => [newDoc, ...prev]);
  };

  return (
    <CaseContext.Provider
      value={{
        cases,
        activeCase,
        setActiveCase,
        activeTab,
        setActiveTab,
        entities,
        selectedEntity,
        setSelectedEntity,
        isDrawerOpen,
        setIsDrawerOpen,
        evidenceDocs,
        selectedDoc,
        setSelectedDoc,
        timelineEvents,
        priorityLeads,
        inspectInGraph,
        viewDocumentDossier,
        addEvidenceDocument,
      }}
    >
      {children}
    </CaseContext.Provider>
  );
};

export const useCase = () => {
  const context = useContext(CaseContext);
  if (!context) {
    throw new Error('useCase must be used within a CaseProvider');
  }
  return context;
};
