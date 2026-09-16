import React, { createContext, useContext, useState } from 'react';
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
  MOCK_PRIORITY_LEADS
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
  const [cases] = useState<CaseFile[]>(INITIAL_CASES);
  const [activeCase, setActiveCase] = useState<CaseFile>(INITIAL_CASES[0]);
  const [activeTab, setActiveTab] = useState<WorkspaceTab>('copilot');
  const [entities] = useState<EntityDossier[]>(MOCK_ENTITIES);
  const [selectedEntity, setSelectedEntity] = useState<EntityDossier | null>(MOCK_ENTITIES[0]);
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);
  const [evidenceDocs, setEvidenceDocs] = useState<EvidenceDocument[]>(MOCK_EVIDENCE_DOCS);
  const [selectedDoc, setSelectedDoc] = useState<EvidenceDocument | null>(null);
  const [timelineEvents] = useState<TimelineEvent[]>(MOCK_TIMELINE_EVENTS);
  const [priorityLeads] = useState<PriorityLead[]>(MOCK_PRIORITY_LEADS);

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
