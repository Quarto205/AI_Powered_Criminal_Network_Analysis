/**
 * API Client instance factory.
 * Easily toggles between Mock and Real API without touching UI components.
 */

import { IApiClient } from './clientInterface';
import { MockApiClient } from './mockApiClient';
import { RealApiClient } from './realApiClient';

export * from './clientInterface';
export * from './mockApiClient';
export * from './realApiClient';

const useMock = import.meta.env?.VITE_USE_MOCK_API !== 'false';
const isTest = import.meta.env?.MODE === 'test' || import.meta.env?.VITEST === 'true';

export const apiClient: IApiClient = useMock
  ? new MockApiClient(isTest ? 0 : 50)
  : new RealApiClient();
