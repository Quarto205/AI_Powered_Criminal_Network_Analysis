/**
 * Selection Context
 * Manages active graph element selection and slide-out detail drawers.
 */

import React, { createContext, useContext, useState } from 'react';
import { CytoscapeNodeData, CytoscapeEdgeData } from '../contracts/graph';

export type ActiveDrawer = 'ENTITY' | 'EVIDENCE' | 'REVIEW_QUEUE' | 'AI_EXPLANATION' | null;

export interface EvidenceTargetContext {
  type: 'entity' | 'relationship';
  id: string;
}

interface SelectionContextType {
  selectedNode: CytoscapeNodeData | null;
  selectedEdge: CytoscapeEdgeData | null;
  activeDrawer: ActiveDrawer;
  evidenceTarget: EvidenceTargetContext | null;
  selectNode: (node: CytoscapeNodeData) => void;
  selectEdge: (edge: CytoscapeEdgeData) => void;
  openEvidence: (target?: EvidenceTargetContext) => void;
  openReviewQueue: (target?: EvidenceTargetContext) => void;
  openAIExplanation: (target?: EvidenceTargetContext) => void;
  closeDrawer: () => void;
}

const SelectionContext = createContext<SelectionContextType | undefined>(undefined);

export const SelectionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedNode, setSelectedNode] = useState<CytoscapeNodeData | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<CytoscapeEdgeData | null>(null);
  const [activeDrawer, setActiveDrawer] = useState<ActiveDrawer>(null);
  const [evidenceTarget, setEvidenceTarget] = useState<EvidenceTargetContext | null>(null);

  const selectNode = (node: CytoscapeNodeData) => {
    setSelectedNode(node);
    setSelectedEdge(null);
    setEvidenceTarget(null);
    setActiveDrawer('ENTITY');
  };

  const selectEdge = (edge: CytoscapeEdgeData) => {
    setSelectedEdge(edge);
    setSelectedNode(null);
    setEvidenceTarget({ type: 'relationship', id: edge.id });
    setActiveDrawer('EVIDENCE');
  };

  const openEvidence = (target?: EvidenceTargetContext) => {
    if (target) {
      setEvidenceTarget(target);
    } else if (selectedEdge) {
      setEvidenceTarget({ type: 'relationship', id: selectedEdge.id });
    } else if (selectedNode) {
      setEvidenceTarget({ type: 'entity', id: selectedNode.id });
    }
    setActiveDrawer('EVIDENCE');
  };

  const openReviewQueue = (target?: EvidenceTargetContext) => {
    if (target) {
      setEvidenceTarget(target);
    } else if (selectedNode) {
      setEvidenceTarget({ type: 'entity', id: selectedNode.id });
    }
    setActiveDrawer('REVIEW_QUEUE');
  };

  const openAIExplanation = (target?: EvidenceTargetContext) => {
    if (target) {
      setEvidenceTarget(target);
    }
    setActiveDrawer('AI_EXPLANATION');
  };

  const closeDrawer = () => {
    setActiveDrawer(null);
    setEvidenceTarget(null);
  };

  return (
    <SelectionContext.Provider
      value={{
        selectedNode,
        selectedEdge,
        activeDrawer,
        evidenceTarget,
        selectNode,
        selectEdge,
        openEvidence,
        openReviewQueue,
        openAIExplanation,
        closeDrawer,
      }}
    >
      {children}
    </SelectionContext.Provider>
  );
};

export const useSelection = (): SelectionContextType => {
  const context = useContext(SelectionContext);
  if (!context) {
    throw new Error('useSelection must be used within a SelectionProvider');
  }
  return context;
};
