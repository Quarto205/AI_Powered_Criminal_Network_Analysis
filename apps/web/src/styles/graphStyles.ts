/**
 * Cytoscape.js Graph Styling & Visual Invariants (SIH26189)
 * Source: docs/contracts/08_UI_DATA_CONTRACT.md Section 8.2
 * 
 * Non-Negotiable Invariants:
 * 1. Observable relationships (hard facts: OBSERVED, CORROBORATED, CONFIRMED) -> SOLID LINE.
 * 2. AI-inferred relationships (INFERRED / PREDICTED) -> DASHED LINE.
 * 3. Status must not depend on color alone; redundant text labels and patterns are mandatory.
 */

export const CYTOSCAPE_GRAPH_STYLES = [
  // Core Node Styles
  {
    selector: 'node',
    style: {
      'label': 'data(label)',
      'color': '#ffffff',
      'font-size': '12px',
      'text-valign': 'bottom',
      'text-margin-y': 6,
      'background-color': '#1e293b',
      'border-width': 2,
      'border-color': '#475569',
      'width': 44,
      'height': 44
    }
  },
  // Node Categories
  {
    selector: 'node[category = "Person"]',
    style: {
      'background-color': '#1d4ed8', // Blue
      'border-color': '#60a5fa'
    }
  },
  {
    selector: 'node[category = "Phone"]',
    style: {
      'background-color': '#047857', // Emerald
      'border-color': '#34d399'
    }
  },
  {
    selector: 'node[category = "BankAccount"]',
    style: {
      'background-color': '#b45309', // Amber
      'border-color': '#fbbf24'
    }
  },
  {
    selector: 'node[category = "Vehicle"]',
    style: {
      'background-color': '#6d28d9', // Purple
      'border-color': '#a78bfa'
    }
  },
  {
    selector: 'node[category = "Location"]',
    style: {
      'background-color': '#be123c', // Rose
      'border-color': '#fb7185'
    }
  },

  // Base Edge Styles
  {
    selector: 'edge',
    style: {
      'width': 2,
      'curve-style': 'bezier',
      'target-arrow-shape': 'triangle',
      'arrow-scale': 1.2,
      'label': 'data(type)',
      'font-size': '10px',
      'color': '#94a3b8',
      'text-background-opacity': 0.8,
      'text-background-color': '#0f172a',
      'text-background-padding': '2px',
      'text-background-shape': 'roundrectangle'
    }
  },

  // Visual Invariant 1: Physical / Source Evidence (SOLID LINE)
  {
    selector: 'edge[evidenceState = "OBSERVED"], edge[evidenceState = "CORROBORATED"], edge[evidenceState = "CONFIRMED"]',
    style: {
      'line-style': 'solid',
      'line-color': '#64748b',
      'target-arrow-color': '#64748b',
      'width': 2.5
    }
  },
  {
    selector: 'edge[evidenceState = "CONFIRMED"]',
    style: {
      'line-color': '#22c55e', // Green
      'target-arrow-color': '#22c55e',
      'width': 3
    }
  },

  // Visual Invariant 2: AI-Inferred Links (DASHED LINE + Redundant Accessibility Indicator)
  {
    selector: 'edge[evidenceState = "INFERRED"]',
    style: {
      'line-style': 'dashed',
      'line-dash-pattern': [6, 4],
      'line-color': '#f59e0b', // Amber
      'target-arrow-color': '#f59e0b',
      'width': 2,
      'label': 'data(type) [INFERRED]' // Redundant text badge for accessibility
    }
  },

  // Rejected / Unconfirmed Evidence (DOTTED LINE)
  {
    selector: 'edge[evidenceState = "REJECTED"]',
    style: {
      'line-style': 'dotted',
      'line-dash-pattern': [2, 3],
      'line-color': '#ef4444',
      'target-arrow-color': '#ef4444',
      'opacity': 0.5,
      'label': 'data(type) [REJECTED]'
    }
  }
];
