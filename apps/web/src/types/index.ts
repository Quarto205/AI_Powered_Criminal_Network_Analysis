// Domain Types for CNAS Forensic Intelligence Workstation

export type PerformanceMode = 'full' | 'balanced' | 'reduced';

export interface Investigator {
  id: string;
  name: string;
  badgeNumber: string;
  role: string;
  unit: string;
  avatarUrl: string;
}

export interface CaseFile {
  id: string;
  caseNumber: string;
  title: string;
  jurisdiction: string;
  unit: string;
  status: 'ACTIVE' | 'TRIAGE' | 'SUBMITTED_COURT' | 'ARCHIVED';
  stage: string;
  leadInvestigator: Investigator;
  entityCount: number;
  evidenceCount: number;
  criticalLeadsCount: number;
  description: string;
  createdAt: string;
  updatedAt: string;
}

export type EntityType = 
  | 'PERSON'
  | 'SHELL_COMPANY'
  | 'BANK_ACCOUNT'
  | 'PHONE'
  | 'CRYPTO_WALLET'
  | 'LOGISTICS_HUB'
  | 'COMPANY'
  | 'ACCOUNT'
  | 'EVENT';

export interface EntityDossier {
  id: string;
  caseId: string;
  name: string;
  type: EntityType;
  primaryRole: string;
  threatLevel: 'CRITICAL' | 'ELEVATED' | 'MONITORED' | 'CLEARED';
  degreeCentrality: number;
  betweenness: number;
  clusteringCoeff: number;
  photoUrl?: string;
  isObserved: boolean;
  biometricVerified: boolean;
  aliases: string[];
  identifiers: {
    pan?: string;
    passport?: string;
    msisdn?: string;
    msisdnStatus?: string;
    imei?: string;
    accountNumber?: string;
    bankName?: string;
    cryptoAddress?: string;
    registrationNumber?: string;
  };
  aiClusterInsight?: {
    matchScore: number;
    explanation: string;
    code: string;
  };
  evidenceCount: number;
  connectionsCount: number;
}

export type RelationEpistemicType = 'VERIFIED_OBSERVED' | 'AI_INFERRED';

export interface NetworkEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  relationshipType?: 'OWNS' | 'TRANSFERRED_TO' | 'COMMUNICATED_WITH';
  amount?: string;
  epistemicType: RelationEpistemicType;
  confidence: number; // 0.0 to 1.0
  evidenceId?: string;
  details?: string;
}

export interface EvidenceDocument {
  id: string;
  caseId: string;
  title: string;
  filename: string;
  category: 'BANKING' | 'CDR' | 'LEGAL' | 'CUSTOMS';
  sha256: string;
  fileSize: string;
  timestamp: string;
  verifiedChainOfCustody: boolean;
  section65BCertified: boolean;
  linkedEntityIds: string[];
  excerpt: string;
  metadata: Record<string, string>;
  detectedHighlights?: {
    text: string;
    entityId: string;
    entityName: string;
    color: string;
  }[];
}

export interface TimelineEvent {
  id: string;
  caseId: string;
  timestamp: string;
  displayTime: string;
  title: string;
  description: string;
  type: 'FINANCIAL' | 'SIGINT' | 'LEGAL' | 'SURVEILLANCE';
  severity: 'CRITICAL' | 'WARN' | 'INFO';
  linkedEntityId?: string;
  linkedEntityName?: string;
  evidenceId?: string;
  sourceType: string;
  hasAudio?: boolean;
}

export interface PriorityLead {
  id: string;
  rank: number;
  title: string;
  description: string;
  confidenceScore: number; // e.g. 94%
  category: 'GNN_ASSOCIATION' | 'FAN_OUT' | 'GEO_FENCE' | 'SMURFING';
  identifiedAgo: string;
  urgency: 'URGENT' | 'HIGH' | 'ROUTINE';
  targetEntities: string[];
  status: 'PENDING_REVIEW' | 'DISPATCHED' | 'DISMISSED';
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  investigatorId: string;
  investigatorName: string;
  action: string;
  details: string;
  hash: string;
  ipAddress: string;
}

export interface CopilotMessage {
  id: string;
  sender: 'INVESTIGATOR' | 'COPILOT';
  text: string;
  timestamp: string;
  citations?: {
    label: string;
    documentId?: string;
    entityId?: string;
  }[];
  suggestedPrompts?: string[];
}

export interface CopilotSession {
  id: string;
  caseId: string;
  title: string;
  preview: string;
  timeLabel: string;
  category: 'TODAY' | 'YESTERDAY' | 'PAST_7_DAYS';
  isActive?: boolean;
}

export interface BackgroundJob {
  id: string;
  title: string;
  progress: number;
  status: 'RUNNING' | 'COMPLETED' | 'QUEUED';
  type: 'OCR' | 'GNN_INDEX' | 'HASH_VERIFY';
  startedAgo: string;
}
