/**
 * SIH26189 Canonical Shared Types & Enums
 * Strictly adheres to 01_SHARED_TYPES.md, 07_AUTH_SECURITY.md, 09_NAMING_CONVENTIONS.md
 */

export type UUID = string;

/** Section 1.2: System Master States */
export const MasterStates = {
  UNAUTHENTICATED: 'UNAUTHENTICATED',
  AUTHENTICATED: 'AUTHENTICATED',
  CASE_SELECTED: 'CASE_SELECTED',
  INGESTION: 'INGESTION',
  PROCESSING: 'PROCESSING',
  REVIEW: 'REVIEW',
  GRAPH_READY: 'GRAPH_READY',
  ANALYSIS: 'ANALYSIS',
  INVESTIGATOR_REVIEW: 'INVESTIGATOR_REVIEW',
  REPORTING_AUDIT: 'REPORTING/AUDIT',
} as const;

export type MasterState = (typeof MasterStates)[keyof typeof MasterStates];

/** Section 1.3: Document Lifecycle States */
export const DocumentStates = {
  RECEIVED: 'RECEIVED',
  VALIDATED: 'VALIDATED',
  PROCESSING: 'PROCESSING',
  EXTRACTED: 'EXTRACTED',
  REVIEW_REQUIRED: 'REVIEW_REQUIRED',
  ACCEPTED: 'ACCEPTED',
  REJECTED: 'REJECTED',
  FAILED: 'FAILED',
} as const;

export type DocumentState = (typeof DocumentStates)[keyof typeof DocumentStates];

/** Section 1.4: Relationship Evidence States */
export const RelationshipStates = {
  OBSERVED: 'OBSERVED',
  CORROBORATED: 'CORROBORATED',
  CONFIRMED: 'CONFIRMED',
  REJECTED: 'REJECTED',
  INFERRED: 'INFERRED',
} as const;

export type RelationshipState = (typeof RelationshipStates)[keyof typeof RelationshipStates];

/** Section 1.5: Review States */
export const ReviewStates = {
  NEW: 'NEW',
  REVIEWED: 'REVIEWED',
  CONFIRMED: 'CONFIRMED',
  REJECTED: 'REJECTED',
} as const;

export type ReviewState = (typeof ReviewStates)[keyof typeof ReviewStates];

/** Section 7.1: RBAC Roles */
export const UserRoles = {
  INVESTIGATOR: 'INVESTIGATOR',
  ANALYST: 'ANALYST',
  SUPERVISOR: 'SUPERVISOR',
} as const;

export type UserRole = (typeof UserRoles)[keyof typeof UserRoles];

/** Section 3.1: Node Entity Types */
export const EntityTypes = {
  PERSON: 'PERSON',
  PHONE: 'PHONE',
  BANK_ACCOUNT: 'BANK_ACCOUNT',
  VEHICLE: 'VEHICLE',
  ORGANIZATION: 'ORGANIZATION',
  LOCATION: 'LOCATION',
  CASE: 'CASE',
  EVIDENCE: 'EVIDENCE',
  OFFENSE: 'OFFENSE',
} as const;

export type EntityType = (typeof EntityTypes)[keyof typeof EntityTypes];

/** Section 3.2: Relationship Types */
export const RelationshipTypes = {
  ACCUSED_IN: 'ACCUSED_IN',
  KNOWS: 'KNOWS',
  CONTACTED: 'CONTACTED',
  LOCATED_AT: 'LOCATED_AT',
  OWNS: 'OWNS',
  USED_BY: 'USED_BY',
  COMMUNICATED_WITH: 'COMMUNICATED_WITH',
  PINGED_TOWER: 'PINGED_TOWER',
  TRANSFERRED_TO: 'TRANSFERRED_TO',
  OWNED_BY: 'OWNED_BY',
  REGISTERED_TO: 'REGISTERED_TO',
  SCANNED_AT: 'SCANNED_AT',
  AFFILIATED_WITH: 'AFFILIATED_WITH',
  CONTAINS: 'CONTAINS',
  SUPPORTS: 'SUPPORTS',
  REFUTES: 'REFUTES',
} as const;

export type RelationshipType = (typeof RelationshipTypes)[keyof typeof RelationshipTypes];
