export interface ApiError {
  message: string;
  code: number;
}

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    // Load token from local storage if available
    const storedToken = localStorage.getItem('cnas_auth_token');
    if (storedToken) {
      this.token = storedToken;
    }
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('cnas_auth_token', token);
    } else {
      localStorage.removeItem('cnas_auth_token');
    }
  }

  getToken(): string | null {
    return this.token;
  }

  async fetch<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const headers = new Headers(options.headers || {});
    
    // Set default Content-Type if not provided
    if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }

    // Inject auth token
    if (this.token) {
      headers.set('Authorization', `Bearer ${this.token}`);
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        if (response.status === 401) {
          // Trigger a logout event or clear token
          this.setToken(null);
          window.dispatchEvent(new Event('cnas:unauthorized'));
        }
        
        let errorData;
        try {
          errorData = await response.json();
        } catch {
          errorData = { detail: response.statusText };
        }
        
        throw {
          code: response.status,
          message: errorData.detail || 'API Request Failed'
        } as ApiError;
      }

      // If response is 204 No Content, return null
      if (response.status === 204) {
        return null as unknown as T;
      }

      // Return JSON data
      return response.json();
    } catch (error) {
      if ((error as ApiError).code) {
        throw error;
      }
      throw {
        code: 500,
        message: error instanceof Error ? error.message : 'Network Error',
      } as ApiError;
    }
  }

  async get<T>(path: string, options?: RequestInit): Promise<T> {
    return this.fetch<T>(path, { ...options, method: 'GET' });
  }

  async post<T>(path: string, data?: any, options?: RequestInit): Promise<T> {
    return this.fetch<T>(path, {
      ...options,
      method: 'POST',
      body: data instanceof FormData ? data : JSON.stringify(data),
    });
  }

  async put<T>(path: string, data?: any, options?: RequestInit): Promise<T> {
    return this.fetch<T>(path, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete<T>(path: string, options?: RequestInit): Promise<T> {
    return this.fetch<T>(path, { ...options, method: 'DELETE' });
  }
}

// Fallback to localhost:8000 for development API
export const apiClient = new ApiClient(import.meta.env.VITE_API_URL || 'http://localhost:8000');
