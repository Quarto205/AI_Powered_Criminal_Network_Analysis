import React, { createContext, useContext, useState } from 'react';
import { Investigator } from '../types';
import { CURRENT_INVESTIGATOR } from '../mocks/data';

interface AuthContextType {
  isAuthenticated: boolean;
  currentUser: Investigator | null;
  login: (email: string, badgeId: string) => boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Default to authenticated for instant preview, but allow full logout/login testing
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(true);
  const [currentUser, setCurrentUser] = useState<Investigator | null>(CURRENT_INVESTIGATOR);

  const login = (_email: string, _badgeId: string) => {
    setIsAuthenticated(true);
    setCurrentUser(CURRENT_INVESTIGATOR);
    return true;
  };

  const logout = () => {
    setIsAuthenticated(false);
    setCurrentUser(null);
  };

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
