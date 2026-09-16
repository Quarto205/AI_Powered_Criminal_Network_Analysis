import {
  CaseFile,
  EntityDossier,
  NetworkEdge,
  EvidenceDocument,
  TimelineEvent,
  PriorityLead,
  AuditLogEntry,
  CopilotSession,
  CopilotMessage,
  BackgroundJob,
  Investigator
} from '../types';

export const CURRENT_INVESTIGATOR: Investigator = {
  id: 'INV-4821',
  name: 'Insp. Ananya Roy',
  badgeNumber: 'DL-SP-9014',
  role: 'Special Cell Lead',
  unit: 'New Delhi Special Cell / Anti-Terror Unit',
  avatarUrl: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80'
};

export const INITIAL_CASES: CaseFile[] = [
  {
    id: 'case-del-0891',
    caseNumber: 'CASE-2026-DEL-0891',
    title: 'Operation Hawala Nexus — Cyber & Financial Syndicate',
    jurisdiction: 'New Delhi — Special Cell / Crime Branch',
    unit: 'Counter-Terror & Financial Crimes Unit',
    status: 'ACTIVE',
    stage: 'Triage Phase 2 (Nodal Surveillance)',
    leadInvestigator: CURRENT_INVESTIGATOR,
    entityCount: 14,
    evidenceCount: 8,
    criticalLeadsCount: 3,
    description: 'Cross-border hawala liquidation syndicate leveraging shell import-export entities and distributed cash couriers across Delhi NCR.',
    createdAt: '2026-05-18T00:00:00Z',
    updatedAt: '2026-05-24T18:30:00Z'
  },
  {
    id: 'case-bom-0412',
    caseNumber: 'CASE-2026-BOM-0412',
    title: 'JNPT Maritime Container Diversion Matrix',
    jurisdiction: 'Mumbai — Crime Branch Unit 9',
    unit: 'Maritime Intelligence Wing',
    status: 'ACTIVE',
    stage: 'Forensic Extraction',
    leadInvestigator: CURRENT_INVESTIGATOR,
    entityCount: 9,
    evidenceCount: 14,
    criticalLeadsCount: 1,
    description: 'Bypassed consignment declarations mapped to bonded customs warehouses in Raigad district.',
    createdAt: '2026-04-10T00:00:00Z',
    updatedAt: '2026-05-23T11:20:00Z'
  },
  {
    id: 'case-blr-0199',
    caseNumber: 'CASE-2026-BLR-0199',
    title: 'De-Fi Smurfing & Layered Gateway Network',
    jurisdiction: 'Bengaluru — CID Cyber Cell',
    unit: 'Digital Forensics Lab',
    status: 'TRIAGE',
    stage: 'Chain Analysis',
    leadInvestigator: CURRENT_INVESTIGATOR,
    entityCount: 22,
    evidenceCount: 19,
    criticalLeadsCount: 4,
    description: 'Decentralized peer-to-peer micro-settlement channels funneling unlicensed proceeds through mule UPI handles.',
    createdAt: '2026-05-01T00:00:00Z',
    updatedAt: '2026-05-22T16:45:00Z'
  }
];

export const MOCK_ENTITIES: EntityDossier[] = [
  {
    id: 'ent-tariq',
    caseId: 'case-del-0891',
    name: 'Tariq M.',
    type: 'PERSON',
    primaryRole: 'Prime Facilitator / Syndicate Core',
    threatLevel: 'CRITICAL',
    degreeCentrality: 8.9,
    betweenness: 0.84,
    clusteringCoeff: 0.78,
    photoUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&auto=format&fit=crop&q=80',
    isObserved: true,
    biometricVerified: true,
    aliases: ['Tariq Bhai', 'Abu Fahad', 'The Merchant'],
    identifiers: {
      pan: 'ABCPT••••4F',
      passport: 'V489••••2',
      msisdn: '+91 98110 •••••',
      msisdnStatus: 'Active 12m ago',
      imei: '863920199201'
    },
    aiClusterInsight: {
      matchScore: 94,
      explanation: 'Identical remittance hashes map Tariq M. to unregistered shell entity Al-Madina FZE via 4 crypto-fiat settlement runs.',
      code: 'EXP-094'
    },
    evidenceCount: 3,
    connectionsCount: 5
  },
  {
    id: 'ent-al-zubair',
    caseId: 'case-del-0891',
    name: 'Al-Zubair Exports FZE',
    type: 'SHELL_COMPANY',
    primaryRole: 'Dubai Conduit / Freezone Shell',
    threatLevel: 'ELEVATED',
    degreeCentrality: 6.2,
    betweenness: 0.61,
    clusteringCoeff: 0.65,
    isObserved: true,
    biometricVerified: false,
    aliases: ['Al-Zubair Maritime General Trading'],
    identifiers: {
      registrationNumber: 'JAFZA-FZ-88190',
      pan: 'AALCA••••1E'
    },
    evidenceCount: 2,
    connectionsCount: 4
  },
  {
    id: 'ent-icici-acct',
    caseId: 'case-del-0891',
    name: 'ICICI Acct ••••4921',
    type: 'BANK_ACCOUNT',
    primaryRole: 'Shell Mirror / Fan-out Source',
    threatLevel: 'CRITICAL',
    degreeCentrality: 7.4,
    betweenness: 0.72,
    clusteringCoeff: 0.82,
    isObserved: true,
    biometricVerified: true,
    aliases: ['Front Corporate Current Account'],
    identifiers: {
      accountNumber: 'ICICI-0049210988',
      bankName: 'ICICI Bank, Connaught Place Branch'
    },
    aiClusterInsight: {
      matchScore: 91,
      explanation: 'Automated velocity trigger tripped: 82 micro-deposits under ₹50,000 threshold within 180 minutes.',
      code: 'SMURF-091'
    },
    evidenceCount: 4,
    connectionsCount: 6
  },
  {
    id: 'ent-vikas',
    caseId: 'case-del-0891',
    name: 'Vikas S.',
    type: 'PERSON',
    primaryRole: 'Logistics Operative & Courier Coordinator',
    threatLevel: 'MONITORED',
    degreeCentrality: 4.8,
    betweenness: 0.42,
    clusteringCoeff: 0.58,
    photoUrl: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=200&auto=format&fit=crop&q=80',
    isObserved: true,
    biometricVerified: true,
    aliases: ['Vicky Delhi'],
    identifiers: {
      pan: 'BKPPS••••9G',
      msisdn: '+91 98992 •••••',
      msisdnStatus: 'Tower BTS 404-45 ping 8m ago'
    },
    evidenceCount: 2,
    connectionsCount: 3
  },
  {
    id: 'ent-chandni-chowk',
    caseId: 'case-del-0891',
    name: 'Chandni Chowk Point',
    type: 'LOGISTICS_HUB',
    primaryRole: 'Physical Cash Dispersal Hub',
    threatLevel: 'CRITICAL',
    degreeCentrality: 5.5,
    betweenness: 0.55,
    clusteringCoeff: 0.71,
    isObserved: true,
    biometricVerified: false,
    aliases: ['Terminal 4 Old Delhi', 'Kucha Ghasiram Depot'],
    identifiers: {
      registrationNumber: 'GEO-28.6562-77.2301'
    },
    evidenceCount: 3,
    connectionsCount: 4
  },
  {
    id: 'ent-al-madina',
    caseId: 'case-del-0891',
    name: 'Al-Madina FZE',
    type: 'SHELL_COMPANY',
    primaryRole: 'Predicted Offshore Entity',
    threatLevel: 'ELEVATED',
    degreeCentrality: 3.8,
    betweenness: 0.35,
    clusteringCoeff: 0.49,
    isObserved: false, // AI Inferred
    biometricVerified: false,
    aliases: ['Al Madina Financial Consultants'],
    identifiers: {
      registrationNumber: 'SHARJAH-FZC-4190'
    },
    aiClusterInsight: {
      matchScore: 94,
      explanation: 'GNN Link Prediction assigns 94% association probability based on matching remittance hash strings with Al-Zubair.',
      code: 'GNN-94'
    },
    evidenceCount: 1,
    connectionsCount: 2
  },
  {
    id: 'ent-crypto-wallet',
    caseId: 'case-del-0891',
    name: 'TRC-20 Wallet 0x8f2d…e41a',
    type: 'CRYPTO_WALLET',
    primaryRole: 'USDT Liquidity Bridge',
    threatLevel: 'ELEVATED',
    degreeCentrality: 4.1,
    betweenness: 0.48,
    clusteringCoeff: 0.60,
    isObserved: false, // AI Inferred
    biometricVerified: false,
    aliases: ['Tether Settlement Pool'],
    identifiers: {
      cryptoAddress: '0x8f2de41a998c01f4b238914ba991'
    },
    aiClusterInsight: {
      matchScore: 89,
      explanation: 'Associated with 4 fiat off-ramps matching ICICI 4921 transaction amounts with ±0.5% currency delta.',
      code: 'CHAIN-089'
    },
    evidenceCount: 1,
    connectionsCount: 3
  }
];

export const MOCK_EDGES: NetworkEdge[] = [
  {
    id: 'edge-1',
    source: 'ent-tariq',
    target: 'ent-al-zubair',
    label: '₹1.8 Cr Hawala Remittance',
    relationshipType: 'TRANSFERRED_TO',
    amount: '₹1,80,00,000',
    epistemicType: 'VERIFIED_OBSERVED',
    confidence: 1.0,
    evidenceId: 'doc-2',
    details: 'Direct corporate power of attorney & 12 matching commercial invoice numbers'
  },
  {
    id: 'edge-2',
    source: 'ent-tariq',
    target: 'ent-icici-acct',
    label: 'Layered Bank Transfers',
    relationshipType: 'TRANSFERRED_TO',
    amount: '₹4,50,00,000',
    epistemicType: 'VERIFIED_OBSERVED',
    confidence: 1.0,
    evidenceId: 'doc-1',
    details: 'Sole signatory authority with online portal token access logs'
  },
  {
    id: 'edge-3',
    source: 'ent-tariq',
    target: 'ent-vikas',
    label: 'VoIP CDR Intercepts (42x)',
    relationshipType: 'COMMUNICATED_WITH',
    epistemicType: 'VERIFIED_OBSERVED',
    confidence: 0.98,
    evidenceId: 'doc-3',
    details: '42 encrypted voice sessions logged through UAE telecom gateway'
  },
  {
    id: 'edge-4',
    source: 'ent-tariq',
    target: 'ent-chandni-chowk',
    label: 'Cash Courier Route',
    relationshipType: 'TRANSFERRED_TO',
    amount: '₹45,00,000',
    epistemicType: 'VERIFIED_OBSERVED',
    confidence: 0.95,
    evidenceId: 'doc-4',
    details: 'Physical cash drops corroborated by Section 91 CrPC surveillance logs'
  },
  {
    id: 'edge-5',
    source: 'ent-icici-acct',
    target: 'ent-al-madina',
    label: 'Predicted Association (94%)',
    relationshipType: 'OWNS',
    amount: '₹2,20,00,000',
    epistemicType: 'AI_INFERRED',
    confidence: 0.94,
    details: 'GNN Latent Cluster Match: Remittance batch hashes correlate with offshore freezone export declaration'
  },
  {
    id: 'edge-6',
    source: 'ent-icici-acct',
    target: 'ent-crypto-wallet',
    label: 'Predicted Crypto-Bridge (89%)',
    relationshipType: 'TRANSFERRED_TO',
    amount: '₹1,40,00,000',
    epistemicType: 'AI_INFERRED',
    confidence: 0.89,
    details: 'Micro-smurfing tranches matched to Tron blockchain liquidity pools'
  }
];

export const MOCK_EVIDENCE_DOCS: EvidenceDocument[] = [
  {
    id: 'doc-1',
    caseId: 'case-del-0891',
    title: 'ICICI Bank Statement May 2026',
    filename: 'ICICI_Stmt_NovDec_4921.pdf',
    category: 'BANKING',
    sha256: '4b2a99e1208fb18029c78201bba29048e71829038481920398481920398491f',
    fileSize: '2.4 MB',
    timestamp: '2026-05-24T18:30:00Z',
    verifiedChainOfCustody: true,
    section65BCertified: true,
    linkedEntityIds: ['ent-tariq', 'ent-icici-acct'],
    excerpt: 'Detailed ledger transcript recording 82 incoming NEFT/IMPS transfers fan-out across 4 sub-accounts.',
    metadata: {
      'Issuing Authority': 'ICICI Bank Law Enforcement Cell',
      'Account Type': 'Commercial Current Account',
      'Signatory': 'Tariq M.',
      'Custodian': 'SI R. Rawat, Special Cell'
    },
    detectedHighlights: [
      { text: 'ICICI ••••4921', entityId: 'ent-icici-acct', entityName: 'ICICI Acct 4921', color: 'blue' },
      { text: 'INR 45,00,000', entityId: 'ent-chandni-chowk', entityName: 'Liquidation Slip', color: 'rose' }
    ]
  },
  {
    id: 'doc-2',
    caseId: 'case-del-0891',
    title: 'UAE Cargo Bill of Lading #JAFZA-9102',
    filename: 'Customs_BillOfLading_JAFZA9102.pdf',
    category: 'CUSTOMS',
    sha256: '7c891e4881029ba817290cb819208392182903848192039848192039849102c',
    fileSize: '3.1 MB',
    timestamp: '2026-05-23T14:10:00Z',
    verifiedChainOfCustody: true,
    section65BCertified: true,
    linkedEntityIds: ['ent-tariq', 'ent-al-zubair'],
    excerpt: 'Certified maritime manifest from Port of Jebel Ali to JNPT Mumbai for 40 containers heavy industrial parts.',
    metadata: {
      'Port of Origin': 'Jebel Ali Free Zone (JAFZA), Dubai UAE',
      'Port of Discharge': 'Jawaharlal Nehru Port Terminal (JNPT), Mumbai',
      'Vessel': 'MV Arabian Pearl',
      'Shipper': 'Al-Zubair Exports FZE',
      'Consignee': 'Hind Logistics & Hardware Traders (Delhi)',
      'Notify Party': 'Tariq M. (PoA Holder)'
    },
    detectedHighlights: [
      { text: 'Al-Zubair Exports FZE', entityId: 'ent-al-zubair', entityName: 'Al-Zubair Exports', color: 'blue' },
      { text: 'Tariq M.', entityId: 'ent-tariq', entityName: 'Tariq M.', color: 'purple' },
      { text: 'JAFZA Sector 4', entityId: 'ent-al-zubair', entityName: 'Dubai Port', color: 'blue' }
    ]
  },
  {
    id: 'doc-3',
    caseId: 'case-del-0891',
    title: 'VoIP Intercept & CDR Analysis Log',
    filename: 'CDR_Analysis_98110_Interception.csv',
    category: 'CDR',
    sha256: '9e8871029c8829019b88291028392019283901928390192839019283901933b',
    fileSize: '18.9 MB',
    timestamp: '2026-05-24T16:15:00Z',
    verifiedChainOfCustody: true,
    section65BCertified: true,
    linkedEntityIds: ['ent-tariq', 'ent-vikas'],
    excerpt: 'Tower BTS CDR dumps corroborating 42 voice sessions between IMEI 863920199201 and UAE gateway numbers.',
    metadata: {
      'Target IMEI': '863920199201',
      'Total Call Records': '1,420 Sessions',
      'Audio Intercept Length': '04m 18s (Key Excerpt)',
      'Forensic Node': 'Delhi NCR Telecom Surveillance Wing'
    }
  },
  {
    id: 'doc-4',
    caseId: 'case-del-0891',
    title: 'Section 91 CrPC Physical Warrant & Seizure Memo',
    filename: 'Warrant_Section91_DelCP_Signed.pdf',
    category: 'LEGAL',
    sha256: 'd17a88291029cb881920cb88192083921829038481920398481920398408a',
    fileSize: '1.1 MB',
    timestamp: '2026-05-24T14:20:00Z',
    verifiedChainOfCustody: true,
    section65BCertified: true,
    linkedEntityIds: ['ent-chandni-chowk', 'ent-al-zubair'],
    excerpt: 'Statutory seizure receipt and search memo served at registered liaison office in Connaught Place.',
    metadata: {
      'Judicial Authority': 'Court of Chief Metropolitan Magistrate, Patiala House',
      'Signatory Officer': 'SI R. Rawat (IO)',
      'Witness Statements': '2 Independent Commercial Tenants Logged'
    }
  }
];

export const MOCK_TIMELINE_EVENTS: TimelineEvent[] = [
  {
    id: 'evt-1',
    caseId: 'case-del-0891',
    timestamp: '2026-05-24T18:30:00Z',
    displayTime: '18:30 IST · Today',
    title: 'Wire transfer flagged INR 45,00,000 via IMPS',
    description: 'Originating from ICICI ••••4921 to 4 distributed mule beneficiaries. Tranche threshold automated bypass tripped.',
    type: 'FINANCIAL',
    severity: 'CRITICAL',
    linkedEntityId: 'ent-icici-acct',
    linkedEntityName: 'ICICI Acct ••••4921',
    evidenceId: 'doc-1',
    sourceType: 'Core Banking Gateway'
  },
  {
    id: 'evt-2',
    caseId: 'case-del-0891',
    timestamp: '2026-05-24T16:15:00Z',
    displayTime: '16:15 IST · Today',
    title: 'Encrypted voice session CDR linked to UAE switchboard',
    description: 'Call duration 04m 18s from IMEI 863920199201 to gateway router in Deira, Dubai. Voice biometrics queued.',
    type: 'SIGINT',
    severity: 'WARN',
    linkedEntityId: 'ent-tariq',
    linkedEntityName: 'Tariq M.',
    evidenceId: 'doc-3',
    sourceType: 'Telecom Surveillance Cell',
    hasAudio: true
  },
  {
    id: 'evt-3',
    caseId: 'case-del-0891',
    timestamp: '2026-05-24T14:20:00Z',
    displayTime: '14:20 IST · Today',
    title: 'Section 91 CrPC notice dispatched to commercial address',
    description: 'Physical warrant served at Al-Zubair registered liaison office in Connaught Place. Signatory receipt logged by SI Rawat.',
    type: 'LEGAL',
    severity: 'INFO',
    linkedEntityId: 'ent-al-zubair',
    linkedEntityName: 'Al-Zubair Exports FZE',
    evidenceId: 'doc-4',
    sourceType: 'Court Warrant Protocol'
  },
  {
    id: 'evt-4',
    caseId: 'case-del-0891',
    timestamp: '2026-05-23T11:00:00Z',
    displayTime: '11:00 IST · Yesterday',
    title: 'Consignment cleared Customs at JNPT Mumbai',
    description: '40 containers industrial machinery under Bill of Lading JAFZA-9102 released to Hind Logistics transport trucks.',
    type: 'SURVEILLANCE',
    severity: 'INFO',
    linkedEntityId: 'ent-al-zubair',
    linkedEntityName: 'Al-Zubair Exports FZE',
    evidenceId: 'doc-2',
    sourceType: 'Customs CIU'
  },
  {
    id: 'evt-5',
    caseId: 'case-del-0891',
    timestamp: '2026-05-22T08:00:00Z',
    displayTime: '08:00 IST · 22 May',
    title: 'Burner MSISDN activation on Chandni Chowk BTS',
    description: 'Fresh SIM registration under forged credentials detected communicating with Dubai routing gateway.',
    type: 'SIGINT',
    severity: 'WARN',
    linkedEntityId: 'ent-vikas',
    linkedEntityName: 'Vikas S.',
    sourceType: 'Tower BTS Log'
  }
];

export const MOCK_PRIORITY_LEADS: PriorityLead[] = [
  {
    id: 'lead-1',
    rank: 1,
    title: 'Potential Unobserved Association: Al-Madina FZE',
    description: 'Automated GNN correlation detected between mirror account ICICI ••••4921 and offshore export entity Al-Madina FZE with 94% association score.',
    confidenceScore: 94,
    category: 'GNN_ASSOCIATION',
    identifiedAgo: '45m ago',
    urgency: 'URGENT',
    targetEntities: ['ent-icici-acct', 'ent-al-madina'],
    status: 'PENDING_REVIEW'
  },
  {
    id: 'lead-2',
    rank: 2,
    title: 'Rapid Fan-Out Liquidation: Chandni Chowk',
    description: 'INR 45,00,000 cash dispersal in motion across 4 Chandni Chowk terminals. Surveillance unit alerted for physical intercept.',
    confidenceScore: 91,
    category: 'FAN_OUT',
    identifiedAgo: '2h ago',
    urgency: 'URGENT',
    targetEntities: ['ent-chandni-chowk', 'ent-vikas'],
    status: 'PENDING_REVIEW'
  },
  {
    id: 'lead-3',
    rank: 3,
    title: 'Smurfing Pattern: 82 Micro-Deposits',
    description: 'Systematic structured deposits timed within 3 hours under statutory ₹50,000 AML reporting threshold.',
    confidenceScore: 88,
    category: 'SMURFING',
    identifiedAgo: '4h ago',
    urgency: 'HIGH',
    targetEntities: ['ent-icici-acct'],
    status: 'PENDING_REVIEW'
  }
];

export const MOCK_AUDIT_LOGS: AuditLogEntry[] = [
  {
    id: 'aud-1',
    timestamp: '2026-05-24T18:32:10Z',
    investigatorId: 'INV-4821',
    investigatorName: 'Insp. Ananya Roy',
    action: 'GRAPH_EXPANSION',
    details: 'Expanded 2-hop neighborhood centered on Tariq M. with AI confidence threshold >= 85%',
    hash: '0x3a89f...b01c',
    ipAddress: '10.240.12.89 (Govt Intranet)'
  },
  {
    id: 'aud-2',
    timestamp: '2026-05-24T17:45:00Z',
    investigatorId: 'INV-4821',
    investigatorName: 'Insp. Ananya Roy',
    action: 'EVIDENCE_VIEW',
    details: 'Accessed and verified cryptographic hash for UAE Cargo Bill of Lading #JAFZA-9102',
    hash: '0x9c41a...d88e',
    ipAddress: '10.240.12.89 (Govt Intranet)'
  },
  {
    id: 'aud-3',
    timestamp: '2026-05-24T16:20:15Z',
    investigatorId: 'INV-4821',
    investigatorName: 'Insp. Ananya Roy',
    action: 'DOSSIER_PIN',
    details: 'Pinned subject Tariq M. as primary facilitator in Case DEL-0891',
    hash: '0x221bc...f901',
    ipAddress: '10.240.12.89 (Govt Intranet)'
  }
];

export const MOCK_COPILOT_SESSIONS: CopilotSession[] = [
  {
    id: 'sess-1',
    caseId: 'case-del-0891',
    title: 'Cross-border Hawala wire dispersal',
    preview: 'Synthesizing UAE manifest vs ATM dumps',
    timeLabel: '14:32 IST',
    category: 'TODAY',
    isActive: true
  },
  {
    id: 'sess-2',
    caseId: 'case-del-0891',
    title: 'ICICI acct 4921 smurfing correlation',
    preview: '82 micro-deposits flag below ₹50,000 threshold',
    timeLabel: '11:15 IST',
    category: 'TODAY'
  },
  {
    id: 'sess-3',
    caseId: 'case-del-0891',
    title: 'Al-Madina FZE ownership & Dubai freezone',
    preview: 'JAFZA registry scrape & beneficial owner match',
    timeLabel: 'May 23',
    category: 'YESTERDAY'
  },
  {
    id: 'sess-4',
    caseId: 'case-del-0891',
    title: 'Burner IMEI geo-fence overlap',
    preview: 'Tower BTS 404-45-9201 concurrent pings',
    timeLabel: 'May 23',
    category: 'YESTERDAY'
  },
  {
    id: 'sess-5',
    caseId: 'case-del-0891',
    title: 'Section 91 CrPC compliance audit',
    preview: 'Statutory notice checklist and delivery receipts',
    timeLabel: 'May 20',
    category: 'PAST_7_DAYS'
  }
];

export const MOCK_COPILOT_MESSAGES: CopilotMessage[] = [
  {
    id: 'msg-1',
    sender: 'INVESTIGATOR',
    text: 'Correlate the latest ICICI 4921 statement entries with the JAFZA cargo bill of lading. Are there overlapping transaction values or beneficial entities?',
    timestamp: '14:30 IST'
  },
  {
    id: 'msg-2',
    sender: 'COPILOT',
    text: 'Analysis complete across 2 primary evidentiary records:\n\n1. **Direct Entity Overlap**: Tariq M. is cited as the authorized corporate signatory in Bill of Lading #JAFZA-9102 and acts as the registered online token holder for ICICI Account ••••4921.\n\n2. **Financial Flow Corroboration**: Inward consignment CM-88219-DXB (MV Arabian Pearl) cleared JNPT on 22-May. Within 28 hours, ICICI ••••4921 disbursed ₹45,00,000 across 4 Chandni Chowk terminals.\n\n3. **Predicted Association**: GNN Link Prediction highlights shell entity **Al-Madina FZE** as a 94% probabilistic match for the offshore source beneficiary.',
    timestamp: '14:32 IST',
    citations: [
      { label: 'ICICI_Stmt_NovDec_4921.pdf', documentId: 'doc-1' },
      { label: 'Customs_BillOfLading_JAFZA9102.pdf', documentId: 'doc-2' }
    ],
    suggestedPrompts: [
      'Focus graph on Tariq M. and Al-Madina FZE',
      'Generate statutory Section 91 CrPC request draft',
      'Extract all tower BTS pings for IMEI 863920199201'
    ]
  }
];

export const MOCK_BACKGROUND_JOBS: BackgroundJob[] = [
  {
    id: 'job-1',
    title: 'OCR & Entity Extraction: Customs Inward Manifest',
    progress: 100,
    status: 'COMPLETED',
    type: 'OCR',
    startedAgo: '12m ago'
  },
  {
    id: 'job-2',
    title: 'GNN Latent Graph Clustering (k=4 depth)',
    progress: 86,
    status: 'RUNNING',
    type: 'GNN_INDEX',
    startedAgo: '4m ago'
  },
  {
    id: 'job-3',
    title: 'Section 65B Indian Evidence Act Hash Attestation',
    progress: 100,
    status: 'COMPLETED',
    type: 'HASH_VERIFY',
    startedAgo: '18m ago'
  }
];
