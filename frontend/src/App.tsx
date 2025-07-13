import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Tron-themed screens
import TronWelcomeScreen from './screens/TronWelcomeScreen';
import TronConfigScreen from './screens/TronConfigScreen';
import TronCleanupWorkItemsScreen from './screens/TronCleanupWorkItemsScreen';
import TronCleanupTestCasesScreen from './screens/TronCleanupTestCasesScreen';
import TronBacklogSweeperScreen from './screens/TronBacklogSweeperScreen';
import TronExecutableScreen from './screens/TronExecutableScreen';

// Legacy screens (kept for compatibility)
import TestScreen from './screens/TestScreen';
import SimpleProjectWizard from './screens/project/SimpleProjectWizard';

// Layout imports
import MainLayout from './components/layout/MainLayout';

function App() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Router>
        <Routes>
          {/* Main Tron Interface */}
          <Route path="/" element={<TronWelcomeScreen />} />
          
          {/* Configuration Screen */}
          <Route path="/configure" element={<TronConfigScreen />} />
          
          {/* Cleanup Screens */}
          <Route path="/cleanup-workitems" element={<TronCleanupWorkItemsScreen />} />
          <Route path="/cleanup-tests" element={<TronCleanupTestCasesScreen />} />
          
          {/* Backlog Sweeper */}
          <Route path="/sweeper" element={<TronBacklogSweeperScreen />} />
          
          {/* Executable Launcher */}
          <Route path="/launcher" element={<TronExecutableScreen />} />
          
          {/* New Project (reuse existing) */}
          <Route path="/new-project" element={
            <MainLayout>
              <SimpleProjectWizard />
            </MainLayout>
          } />
          
          {/* Legacy test route */}
          <Route path="/test" element={
            <MainLayout>
              <TestScreen />
            </MainLayout>
          } />
        </Routes>
      </Router>
    </div>
  );
}

export default App;
