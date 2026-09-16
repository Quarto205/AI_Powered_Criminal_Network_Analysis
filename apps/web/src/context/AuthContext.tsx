import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../services/apiClient';
import { Investigator } from '../types';
import { CURRENT_INVESTIGATOR } from '../mocks/data';

interface AuthContextType {
  isAuthenticated: boolean;
  currentUser: Investigator | null;
  login: (email: string, badgeId: string) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [currentUser, setCurrentUser] = useState<Investigator | null>(null);
  const [isInitializing, setIsInitializing] = useState<boolean>(true);

  useEffect(() => {
    // Attempt to load current user if token exists
    const token = apiClient.getToken();
    if (token) {
      apiClient.get<any>('/api/v1/auth/me')
        .then((res) => {
          if (res.success && res.data) {
            setCurrentUser({
              id: res.data.user_id,
              name: res.data.username,
              badgeId: 'AUTHED', // Mocked badge
              department: 'Investigator',
              clearance: 'Level 5',
              avatar: 'https://i.pravatar.cc/150?u=' + res.data.user_id
            });
            setIsAuthenticated(true);
          }
        })
        .catch(() => {
          apiClient.setToken(null);
        })
        .finally(() => setIsInitializing(false));
    } else {
      setIsInitializing(false);
    }
  }, []);

  const login = async (email: string, badgeId: string) => {
    try {
      const res = await apiClient.post<any>('/api/v1/auth/login', {
        username: email,
        password: badgeId
      });

      if (res.success && res.data) {
        apiClient.setToken(res.data.access_token);
        setCurrentUser({
          id: res.data.user.user_id,
          name: res.data.user.username,
          badgeId: badgeId,
          department: 'Investigator',
          clearance: 'Level 5',
          avatar: 'https://i.pravatar.cc/150?u=' + res.data.user.user_id
        });
        setIsAuthenticated(true);
        return true;
      }
      return false;
    } catch (e) {
      console.error('Login failed:', e);
      return false;
    }
  };

  const logout = () => {
    apiClient.setToken(null);
    setIsAuthenticated(false);
    setCurrentUser(null);
  };

  if (isInitializing) {
    return null; // Or a loading spinner
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, currentUser, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
