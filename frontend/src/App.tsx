import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Tron-themed screens
import TronWelcomeScreen from './screens/TronWelcomeScreen';
import TronConfigScreen from './screens/TronConfigScreen';
import TronCleanupWorkItemsScreen from './screens/TronCleanupWorkItemsScreen';
import TronCleanupTestCasesScreen from './screens/TronCleanupTestCasesScreen';
import TronBacklogSweeperScreen from './screens/TronBacklogSweeperScreen';
import TronExecutableScreen from './screens/TronExecutableScreen';
import TronSettingsScreen from './screens/settings/TronSettingsScreen';
import MyProjectsScreen from './screens/project/MyProjectsScreen';

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
          {/* Dashboard - Main Tron Interface */}
          <Route path="/dashboard" element={<TronWelcomeScreen />} />
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
          
          {/* Settings Screen */}
          <Route path="/settings" element={<TronSettingsScreen />} />
          
          {/* Projects and Backlog Generator */}
          <Route path="/projects" element={<MyProjectsScreen />} />
          <Route path="/backlog-generator" element={<TronBacklogSweeperScreen />} />
          <Route path="/search" element={<TronWelcomeScreen />} />
          
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
