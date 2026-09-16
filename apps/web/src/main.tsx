import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import { PerformanceProvider } from './context/PerformanceContext';
import { AuthProvider } from './context/AuthContext';
import { CaseProvider } from './context/CaseContext';
import { SearchProvider } from './context/SearchContext';
import './styles/global.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <PerformanceProvider>
      <AuthProvider>
        <CaseProvider>
          <SearchProvider>
            <App />
          </SearchProvider>
        </CaseProvider>
      </AuthProvider>
    </PerformanceProvider>
  </React.StrictMode>
);
