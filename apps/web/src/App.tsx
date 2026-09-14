import React from 'react';
import { CaseProvider } from './context/CaseContext';
import { SelectionProvider } from './context/SelectionContext';
import { AppShell } from './components/shell/AppShell';

export const App: React.FC = () => {
  return (
    <CaseProvider>
      <SelectionProvider>
        <AppShell />
      </SelectionProvider>
    </CaseProvider>
  );
};

export default App;
