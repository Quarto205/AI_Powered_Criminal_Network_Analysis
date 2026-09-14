/**
 * Mock API Envelope Generator (SIH26189)
 * Source: docs/contracts/04_API_SPEC.md
 * 
 * NOTE: Mocks are development fixtures and NOT real API implementations.
 */

import { APIResponseEnvelope, APIErrorDetails } from '../types/contracts';

/**
 * Creates a successful canonical API response envelope.
 */
export function createMockSuccessEnvelope<T>(data: T, requestId?: string): APIResponseEnvelope<T> {
  return {
    success: true,
    data,
    error: null,
    request_id: requestId || `req_mock_${Math.random().toString(36).substring(2, 10)}`
  };
}

/**
 * Creates a standard error canonical API response envelope.
 */
export function createMockErrorEnvelope<T = null>(
  code: string,
  message: string,
  details: Record<string, unknown> | null = null,
  requestId?: string
): APIResponseEnvelope<T> {
  const error: APIErrorDetails = {
    code,
    message,
    details
  };
  return {
    success: false,
    data: null,
    error,
    request_id: requestId || `req_err_${Math.random().toString(36).substring(2, 10)}`
  };
}
