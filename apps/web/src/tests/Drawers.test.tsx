import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EntityDrawer } from '../components/drawers/EntityDrawer';
import { EvidencePanel } from '../components/drawers/EvidencePanel';
import { CaseProvider } from '../context/CaseContext';
import { SelectionProvider } from '../context/SelectionContext';

describe('Drawer Components Tests', () => {
  it('renders EntityDrawer with canonical properties and priority scores', async () => {
    render(
      <CaseProvider>
        <SelectionProvider>
          <EntityDrawer
            nodeData={{
              id: 'ent-person-001',
              label: 'Rajesh Sharma',
              entity_type: 'PERSON',
              case_id: '3fa85f64-5717-4562-b3fc-2c963f66afa6',
              status: 'ACTIVE',
              risk_score: 0.89,
            }}
          />
        </SelectionProvider>
      </CaseProvider>
    );

    expect(screen.getByTestId('entity-drawer')).toBeInTheDocument();
    expect(screen.getByText('Rajesh Sharma')).toBeInTheDocument();

    expect(await screen.findByText(/Corroborated Aliases/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Raju Seth/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/9811XXXX54/i).length).toBeGreaterThan(0);
  });

  it('renders EvidencePanel for factual relationships with document provenance', async () => {
    render(
      <CaseProvider>
        <SelectionProvider>
          <EvidencePanel
            edgeData={{
              id: 'rel-002',
              source: 'ent-phone-001',
              target: 'ent-phone-002',
              type: 'COMMUNICATED_WITH',
              confidence_score: 1.0,
              is_predicted: false,
              provenance_count: 4,
              style_line: 'solid',
            }}
          />
        </SelectionProvider>
      </CaseProvider>
    );

    expect(screen.getByTestId('evidence-panel')).toBeInTheDocument();
    expect(screen.getByText(/Observed Relationship/i)).toBeInTheDocument();
    expect(screen.getByText(/\[OBSERVED FACT\]/i)).toBeInTheDocument();

    expect(await screen.findByText(/Supporting Evidence Documents/i)).toBeInTheDocument();
    expect(screen.getAllByText(/CDR_Export_9811XXXX54_Aug2026.csv/i).length).toBeGreaterThan(0);
  });

  it('renders EvidencePanel for AI-inferred relationships with non-accusatory disclaimer', async () => {
    render(
      <CaseProvider>
        <SelectionProvider>
          <EvidencePanel
            edgeData={{
              id: 'pred-001',
              source: 'ent-person-001',
              target: 'ent-person-003',
              type: 'CONTACTED',
              confidence_score: 0.82,
              is_predicted: true,
              provenance_count: 0,
              style_line: 'dashed',
              model_name: 'GATv2 Link Predictor',
              model_version: 'v1.0.4',
              explanation: 'Model predicted latent coordination based on shared transactions.',
            }}
          />
        </SelectionProvider>
      </CaseProvider>
    );

    expect(screen.getByTestId('evidence-panel')).toBeInTheDocument();
    expect(screen.getByText(/Predicted Association/i)).toBeInTheDocument();
    expect(screen.getByText(/\[AI INFERRED\]/i)).toBeInTheDocument();
    expect(screen.getByText(/Investigative Lead Only/i)).toBeInTheDocument();
  });
});
